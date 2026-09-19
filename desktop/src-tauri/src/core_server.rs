//! Starting and supervising the DAH Python core.
//!
//! The desktop shell is a *host swap* (DEC-001), not a rewrite: it serves the
//! same React bundle the browser host serves, and that bundle keeps talking to
//! the same FastAPI core over HTTP. The only thing the shell adds is spawning
//! that core, waiting for it to answer, and stopping it again.
//!
//! Resolution is split out of `main` on purpose. Which command to run is a pure
//! function of two paths, and the health gate is a pure function of a URL - both
//! are testable without a window, and both are exercised in `cargo test`.

use std::path::{Path, PathBuf};
use std::process::Child;
use std::time::{Duration, Instant};

/// The port every host agrees on. The browser dev proxy, the Vite desktop build
/// and this shell all use 8123, so a request from the bundle always lands on the
/// core regardless of which host served the page.
pub const PORT: u16 = 8123;

/// Name of the PyInstaller-built Python core. Bundled next to the shell
/// executable by `bundle.externalBin`, so in a packaged app this file exists and
/// in a dev checkout it does not - that presence check is the host switch.
pub const SIDECAR_NAME: &str = "dah-core";

/// How long to wait for the dev core (a virtualenv Python) to answer
/// `/health` before giving up. It boots in seconds.
pub const HEALTH_TIMEOUT: Duration = Duration::from_secs(30);

/// Budget for the *packaged* core. `dah-core` is a PyInstaller one-file build:
/// every launch unpacks its archive to a temp directory before a single Python
/// line runs, which costs tens of seconds on a cold disk. The window stays
/// hidden until this passes, so it has to cover the real worst case.
pub const SIDECAR_HEALTH_TIMEOUT: Duration = Duration::from_secs(180);

/// Interval between health attempts. The core boots in a second or two; a
/// shorter interval just burns CPU during startup.
const HEALTH_INTERVAL: Duration = Duration::from_millis(250);

/// Per-request connect/read cap so a hung core cannot eat the whole budget.
const HEALTH_REQUEST_TIMEOUT: Duration = Duration::from_secs(2);

/// A resolved way to start the core. Pure data: `main` turns it into a process.
pub struct ServerCommand {
    pub program: PathBuf,
    pub args: Vec<String>,
    /// Working directory the core must run in so `app.main:app` is importable
    /// (dev path only - the sidecar carries its own interpreter).
    pub current_dir: Option<PathBuf>,
}

impl ServerCommand {
    /// Whether this resolution is the packaged sidecar rather than a dev
    /// virtualenv. Driving the health budget off this keeps a slow one-file
    /// unpack from looking like a dead core.
    pub fn is_sidecar(&self) -> bool {
        self.current_dir.is_none()
    }

    /// How long `wait_for_health` should be given for this resolution.
    pub fn health_timeout(&self) -> Duration {
        if self.is_sidecar() {
            SIDECAR_HEALTH_TIMEOUT
        } else {
            HEALTH_TIMEOUT
        }
    }

    /// Build the `std::process::Command` for this resolution, with the data
    /// directory the core should write to.
    pub fn to_process(&self, data_dir: &Path) -> std::process::Command {
        let mut cmd = std::process::Command::new(&self.program);
        cmd.args(&self.args);
        // The core runs in its own process group. The PyInstaller one-file
        // bootloader forks a child that runs the actual server, and signalling
        // the bootloader alone leaves that child orphaned and holding the port.
        // A group of our own means one signal reaches both.
        #[cfg(unix)]
        {
            use std::os::unix::process::CommandExt;
            cmd.process_group(0);
        }
        if let Some(dir) = &self.current_dir {
            cmd.current_dir(dir);
        }
        // The core owns its own database and dataset storage (DEC-001); the
        // shell only points it at a stable, per-user location.
        cmd.env("DAH_DATA_DIR", data_dir);
        cmd.env("DAH_DB_PATH", data_dir.join("dah.db"));
        // The core ends itself when this pid goes away (app.supervisor). That
        // covers the ways this process can die without running any cleanup of
        // its own - a force kill reaches neither a destructor nor an event.
        cmd.env("DAH_PARENT_PID", std::process::id().to_string());
        cmd
    }
}

/// Decide how to start the Python core.
///
/// * Release - `dah-core`, the PyInstaller sidecar sitting next to this
///   executable (`shell_dir`), runs with no working directory.
/// * Dev - the project's virtualenv Python running uvicorn against the
///   checkout, with `server/` as the working directory.
///
/// The switch is the sidecar file existing, so a packaged app never falls back
/// to a Python that may not be installed, and a dev checkout never needs a
/// packaged binary. `DAH_DEV_CORE=1` overrides it: `tauri dev` copies a built
/// sidecar next to the dev executable, and a developer iterating on the shell
/// usually wants the fast virtualenv core rather than a 40s one-file unpack.
pub fn resolve_server_command(shell_dir: &Path, repo_root: &Path) -> ServerCommand {
    let sidecar = shell_dir.join(SIDECAR_NAME);
    if sidecar.exists() && std::env::var_os("DAH_DEV_CORE").is_none() {
        ServerCommand {
            program: sidecar,
            args: vec!["--port".to_string(), PORT.to_string()],
            current_dir: None,
        }
    } else {
        ServerCommand {
            program: repo_root.join("server").join(".venv").join("bin").join("python"),
            args: vec![
                "-m".to_string(),
                "uvicorn".to_string(),
                "app.main:app".to_string(),
                "--port".to_string(),
                PORT.to_string(),
            ],
            current_dir: Some(repo_root.join("server")),
        }
    }
}

/// Where the core answers its liveness probe.
pub fn health_url(port: u16) -> String {
    format!("http://127.0.0.1:{port}/health")
}

/// Poll the core's liveness endpoint until it answers 200 or the budget runs out.
///
/// Returns `true` once the core is up. A refused connection is expected during
/// startup and is not an error - it just means "try again". Anything else that
/// can be wrong (a hung socket, a non-200) also just retries, because the core
/// is still mid-boot; the timeout, not the error kind, is what bounds this.
pub fn wait_for_health(url: &str, timeout: Duration) -> bool {
    let deadline = Instant::now() + timeout;
    loop {
        if Instant::now() >= deadline {
            return false;
        }
        match ureq::get(url).timeout(HEALTH_REQUEST_TIMEOUT).call() {
            Ok(response) if response.status() == 200 => return true,
            _ => std::thread::sleep(HEALTH_INTERVAL),
        }
    }
}

/// A running core, together with everything it forked.
///
/// Dropping it stops the core. That matters: the shell can terminate without a
/// window close event ever being delivered (macOS app termination does not
/// always route through the window), so cleanup cannot depend on the event
/// handler alone - `Drop` is the safety net.
pub struct ServerChild(Child);

impl ServerChild {
    pub fn new(child: Child) -> Self {
        ServerChild(child)
    }

    /// Stop the core and everything it spawned, then reap.
    pub fn kill(&mut self) -> std::io::Result<()> {
        stop_process_group(self.0.id());
        // SIGKILL the leader and reap it, so the process does not linger as a
        // zombie even if something swallowed the group signal.
        let kill_res = self.0.kill();
        let _ = self.0.wait();
        kill_res
    }
}

impl Drop for ServerChild {
    fn drop(&mut self) {
        // Best effort: the app is going away and there is nobody left to report
        // a failure to.
        let _ = self.kill();
    }
}

#[cfg(unix)]
fn stop_process_group(pid: u32) {
    use nix::sys::signal::{killpg, Signal};
    use nix::unistd::Pid;

    // `process_group(0)` made the core's pid its group id, so signalling the
    // group reaches the bootloader's child too. ESRCH means it is already gone.
    match killpg(Pid::from_raw(pid as i32), Signal::SIGTERM) {
        Ok(()) => {}
        Err(nix::errno::Errno::ESRCH) => {}
        Err(err) => eprintln!("DAH shell: could not signal the core's group: {err}"),
    }
}

#[cfg(not(unix))]
fn stop_process_group(_pid: u32) {}

#[cfg(test)]
mod tests {
    use super::*;
    use std::fs;

    // Both lifecycle tests start a real core on PORT and assert that port is
    // theirs alone afterwards (the orphan check depends on it). Cargo runs
    // tests in parallel by default, so without serialization the two would
    // race for the bind - one would win, the other would die with "address
    // already in use", and the failure would look like a flaky core. Marking
    // them serial makes the port exclusive by construction. CI hit this; a
    // local run passed only by timing luck.
    use serial_test::serial;

    #[test]
    fn dev_resolution_uses_the_project_virtualenv() {
        // A shell directory with no sidecar beside it is a dev checkout.
        let tmp = std::env::temp_dir().join("dah_shell_test_dev");
        fs::create_dir_all(&tmp).unwrap();

        let cmd = resolve_server_command(&tmp, Path::new("/repo"));

        assert!(cmd.program.ends_with("server/.venv/bin/python"), "program: {:?}", cmd.program);
        assert_eq!(
            cmd.args,
            vec![
                "-m", "uvicorn", "app.main:app", "--port", "8123"
            ]
        );
        assert_eq!(cmd.current_dir, Some(PathBuf::from("/repo/server")));
        assert!(!cmd.is_sidecar());
        assert_eq!(cmd.health_timeout(), HEALTH_TIMEOUT);

        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn dev_core_override_ignores_a_present_sidecar() {
        std::env::set_var("DAH_DEV_CORE", "1");
        let tmp = std::env::temp_dir().join("dah_shell_test_override");
        fs::create_dir_all(&tmp).unwrap();
        fs::write(tmp.join(SIDECAR_NAME), b"#!/bin/sh\nexit 0\n").unwrap();

        let cmd = resolve_server_command(&tmp, Path::new("/repo"));

        // The sidecar is there, but the override says: start the virtualenv.
        assert!(cmd.program.ends_with("server/.venv/bin/python"), "program: {:?}", cmd.program);
        assert!(!cmd.is_sidecar());

        std::env::remove_var("DAH_DEV_CORE");
        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn release_resolution_uses_a_bundled_sidecar_when_present() {
        // A shell directory that already contains `dah-core` is a packaged app.
        let tmp = std::env::temp_dir().join("dah_shell_test_release");
        fs::create_dir_all(&tmp).unwrap();
        fs::write(tmp.join(SIDECAR_NAME), b"#!/bin/sh\nexit 0\n").unwrap();

        let cmd = resolve_server_command(&tmp, Path::new("/repo"));

        assert!(cmd.program.ends_with(SIDECAR_NAME), "program: {:?}", cmd.program);
        assert_eq!(cmd.args, vec!["--port", "8123"]);
        // The sidecar carries its own interpreter; no cwd is needed.
        assert!(cmd.current_dir.is_none());
        assert!(cmd.is_sidecar());
        assert_eq!(cmd.health_timeout(), SIDECAR_HEALTH_TIMEOUT);

        let _ = fs::remove_dir_all(&tmp);
    }

    #[test]
    fn health_url_points_at_the_local_core() {
        assert_eq!(health_url(8123), "http://127.0.0.1:8123/health");
    }

    #[test]
    fn health_gate_gives_up_on_a_silent_port() {
        // Nothing listens here, so the gate must fail - and must fail fast,
        // otherwise a broken core stalls the window indefinitely.
        let started = Instant::now();
        assert!(!wait_for_health("http://127.0.0.1:53917/health", Duration::from_secs(2)));
        assert!(
            started.elapsed() < Duration::from_secs(4),
            "gate took {:?}, should have returned near the timeout",
            started.elapsed()
        );
    }

    #[test]
    #[cfg(feature = "e2e")]
    #[serial]
    fn core_starts_and_answers_health() {
        // Proves the whole dev path: resolve the real command for this
        // checkout, spawn it, and wait for the core to answer.
        let repo_root = PathBuf::from(env!("REPO_ROOT"));
        let venv_python = repo_root.join("server").join(".venv").join("bin").join("python");
        if !venv_python.exists() {
            eprintln!("skipping: no virtualenv at {}", venv_python.display());
            return;
        }

        // An empty shell directory: nothing named `dah-core` sits beside the
        // "shell", so resolution must fall to the dev virtualenv. Deliberately
        // not target/debug - a sidecar copied next to a debug build for manual
        // testing would flip this to the sidecar path and make the outcome
        // depend on what happens to be built.
        let shell_dir = std::env::temp_dir().join("dah_shell_e2e_dev_shell");
        fs::create_dir_all(&shell_dir).unwrap();
        let data_dir = std::env::temp_dir().join("dah_shell_e2e_data");
        fs::create_dir_all(&data_dir).unwrap();

        let resolved = resolve_server_command(&shell_dir, &repo_root);
        assert!(resolved.program.ends_with("server/.venv/bin/python"));

        let child = resolved.to_process(&data_dir).spawn().expect("spawn core");
        let mut server = ServerChild(child);

        let up = wait_for_health(&health_url(PORT), HEALTH_TIMEOUT);
        if up {
            // Ask the core itself, not just the gate.
            let body = ureq::get(&health_url(PORT))
                .timeout(HEALTH_REQUEST_TIMEOUT)
                .call()
                .expect("health call")
                .into_string()
                .expect("health body");
            assert!(body.contains("ok"), "health body: {body}");
        }
        server.kill().expect("stop core");
        assert!(up, "core did not answer /health within {:?}", HEALTH_TIMEOUT);

        // The core must not survive being stopped: a process that keeps holding
        // port 8123 makes the next launch fail to bind and look dead.
        assert!(
            port_is_free(PORT, Duration::from_secs(5)),
            "port {PORT} was still bound after the core was stopped"
        );
    }

    #[test]
    #[cfg(feature = "e2e")]
    #[serial]
    fn sidecar_core_stops_without_orphaning() {
        // The dev path is one process; the PyInstaller sidecar is two - a
        // bootloader and the server it forks. Only this test catches an orphan.
        let repo_root = PathBuf::from(env!("REPO_ROOT"));
        // tauri-build bakes the host triple in at compile time; a runtime env
        // lookup would not see it.
        let triple = env!("TAURI_ENV_TARGET_TRIPLE");
        let sidecar = repo_root
            .join("desktop")
            .join("src-tauri")
            .join("binaries")
            .join(format!("dah-core-{triple}"));
        if !sidecar.exists() {
            eprintln!("skipping: no sidecar at {}", sidecar.display());
            return;
        }

        let data_dir = std::env::temp_dir().join("dah_shell_e2e_sidecar");
        fs::create_dir_all(&data_dir).unwrap();

        // `dah-core`, no target suffix, is the name the resolver looks for.
        let shell_dir = std::env::temp_dir().join("dah_shell_e2e_sidecar_shell");
        fs::create_dir_all(&shell_dir).unwrap();
        fs::copy(&sidecar, shell_dir.join(SIDECAR_NAME)).unwrap();

        let resolved = resolve_server_command(&shell_dir, &repo_root);
        assert!(resolved.is_sidecar(), "expected the sidecar resolution");

        let child = resolved.to_process(&data_dir).spawn().expect("spawn sidecar");
        let mut server = ServerChild(child);

        assert!(
            wait_for_health(&health_url(PORT), SIDECAR_HEALTH_TIMEOUT),
            "the sidecar never answered /health"
        );
        server.kill().expect("stop sidecar");

        assert!(
            port_is_free(PORT, Duration::from_secs(10)),
            "port {PORT} was still bound - the sidecar's forked child was orphaned"
        );
    }

    /// True once nothing accepts connections on `port` anymore.
    #[cfg(feature = "e2e")]
    fn port_is_free(port: u16, timeout: Duration) -> bool {
        let deadline = Instant::now() + timeout;
        loop {
            match std::net::TcpStream::connect(("127.0.0.1", port)) {
                Ok(_) => {
                    if Instant::now() >= deadline {
                        return false;
                    }
                    std::thread::sleep(Duration::from_millis(250));
                }
                Err(_) => return true,
            }
        }
    }
}
