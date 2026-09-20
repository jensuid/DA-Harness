//! Where the core's log lives, and how to show it to a user (P5-UX-006).
//!
//! The shell's whole reason for existing is that a user does not have a
//! terminal. The core keeps a log next to their cases (P5-OBSERVE-002) and
//! answers `GET /logs` with its path, but a path in a JSON body is still a
//! terminal answer. This module is the bridge: ask the core, then hand the
//! answer to Finder.
//!
//! Everything here degrades to a sentence rather than an error. A core that is
//! still booting, has hung, or predates the `/logs` endpoint is a *state*, and
//! a menu item that says "logging is off" is better than one that fails when
//! the user needs it most.

use std::path::{Path, PathBuf};
use std::process::Command;
use std::time::Duration;

/// Per-request cap so a hung core cannot freeze the menu.
const REQUEST_TIMEOUT: Duration = Duration::from_secs(2);

/// Where the core answers for its own log.
pub fn logs_url(port: u16) -> String {
    format!("http://127.0.0.1:{port}/logs")
}

/// What `GET /logs` told us.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum LogLocation {
    /// The core is file-logging and this is the file.
    File(PathBuf),
    /// The core answered and file logging is off - an unwritable data
    /// directory, or a core with the endpoint but without a writable home.
    /// Nothing to reveal, and nobody to blame.
    Disabled,
}

/// Read the path out of the core's answer.
///
/// `enabled: false` is reported, not errored, and anything that is not the
/// shape we expect is `Disabled` too - a menu item must never panic on a body
/// it does not recognise.
pub fn parse_log_location(body: &str) -> LogLocation {
    match serde_json::from_str::<serde_json::Value>(body) {
        Ok(value) if value.get("enabled").and_then(|v| v.as_bool()) == Some(true) => match
            value.get("path").and_then(|v| v.as_str())
        {
            Some(path) => LogLocation::File(PathBuf::from(path)),
            None => LogLocation::Disabled,
        },
        _ => LogLocation::Disabled,
    }
}

/// Ask the core where its log is.
///
/// Any transport failure is `Disabled`: during boot the core is not answering
/// yet, and a core older than this endpoint 404s. Both are the same thing from
/// a menu's point of view - nothing to show.
pub fn log_location(port: u16) -> LogLocation {
    match ureq::get(&logs_url(port))
        .timeout(REQUEST_TIMEOUT)
        .call()
    {
        Ok(response) if response.status() == 200 => {
            parse_log_location(&response.into_string().unwrap_or_default())
        }
        _ => LogLocation::Disabled,
    }
}

/// Reveal a path in Finder, selected. `open -R` is macOS-native and needs no
/// extra dependency, and it works on a file deep inside the user's Library -
/// which is where the log actually lives.
pub fn reveal_in_finder(path: &Path) -> std::io::Result<()> {
    let status = Command::new("open").arg("-R").arg(path).status()?;
    if status.success() {
        Ok(())
    } else {
        Err(std::io::Error::new(
            std::io::ErrorKind::Other,
            format!("`open -R` failed with {status}"),
        ))
    }
}

/// What running the menu item produced, so the shell can say it out loud
/// instead of silently doing nothing.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum RevealOutcome {
    /// The log was revealed; this is the file Finder is showing.
    Revealed(PathBuf),
    /// The core is not file-logging. The data directory may be unwritable.
    Disabled,
    /// The core could not be reached at all - it may still be booting, or gone.
    Unreachable,
}

/// The menu item's whole job: ask the core, then show what it said.
pub fn reveal_core_logs(port: u16) -> RevealOutcome {
    match log_location(port) {
        LogLocation::File(path) => match reveal_in_finder(&path) {
            Ok(()) => RevealOutcome::Revealed(path),
            // The path is real and the core is healthy; Finder just refused.
            // That is worth distinguishing from "no core" in the log.
            Err(err) => {
                eprintln!("DAH shell: could not reveal {}: {err}", path.display());
                RevealOutcome::Unreachable
            }
        },
        LogLocation::Disabled => RevealOutcome::Disabled,
    }
}

#[cfg(test)]
#[cfg(feature = "e2e")]
mod e2e {
    use super::*;
    use crate::core_server::{
        health_url, resolve_server_command, wait_for_health, HEALTH_TIMEOUT, ServerChild, PORT,
    };
    use serial_test::serial;
    use std::fs;
    use std::path::PathBuf;

    /// The bridge this module exists to build: the core really does answer
    /// `/logs` with a path a user can be shown, from the shell's own process.
    /// Everything else here is string handling; this is the contract.
    #[test]
    #[serial]
    fn the_live_core_reports_a_log_we_can_reveal() {
        let repo_root = PathBuf::from(env!("REPO_ROOT"));
        let venv_python = repo_root.join("server").join(".venv").join("bin").join("python");
        if !venv_python.exists() {
            eprintln!("skipping: no virtualenv at {}", venv_python.display());
            return;
        }

        // An empty shell directory, as the other e2e tests use: resolution
        // lands on the dev virtualenv rather than on a sidecar that might
        // happen to be built.
        let shell_dir = std::env::temp_dir().join("dah_shell_e2e_dev_shell");
        fs::create_dir_all(&shell_dir).unwrap();
        let data_dir = std::env::temp_dir().join("dah_shell_e2e_logs_data");
        fs::create_dir_all(&data_dir).unwrap();

        let resolved = resolve_server_command(&shell_dir, &repo_root);
        let child = resolved.to_process(&data_dir).spawn().expect("spawn core");
        let mut server = ServerChild::new(child);

        // The core has to be up before it can answer anything about its log.
        // The dev core boots in a second or two; the sidecar budget would
        // make a dead core look like a slow test instead of a failure.
        let up = wait_for_health(&health_url(PORT), HEALTH_TIMEOUT);
        assert!(up, "the core did not answer within {:?}", HEALTH_TIMEOUT);

        let location = log_location(PORT);
        server.kill().expect("stop core");

        match location {
            LogLocation::File(path) => {
                // The path is the one the shell would hand to Finder: under the
                // data dir this test set, and the file the core actually wrote.
                assert!(
                    path.starts_with(&data_dir),
                    "the log {} is not under the data dir {}",
                    path.display(),
                    data_dir.display()
                );
                assert_eq!(path.file_name(), Some("dah-core.log".as_ref()));
                assert!(path.exists(), "the core reported a log that is not there");
            }
            other => panic!(
                "the live core should report a log file, got {other:?} - the                  shell would tell the user logging is off"
            ),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_enabled_answer_carries_the_path() {
        assert_eq!(
            parse_log_location(r#"{"enabled":true,"path":"/tmp/data/logs/dah-core.log","size_bytes":99,"rotated":[],"lines":[]}"#),
            LogLocation::File(PathBuf::from("/tmp/data/logs/dah-core.log"))
        );
    }

    #[test]
    fn a_disabled_answer_is_a_state_not_an_error() {
        assert_eq!(
            parse_log_location(r#"{"enabled":false,"path":null,"size_bytes":0,"rotated":[],"lines":[]}"#),
            LogLocation::Disabled
        );
    }

    #[test]
    fn a_body_that_is_not_the_shape_expected_is_disabled() {
        // A core that grew a different response, a gateway's HTML error page,
        // an empty buffer - none of them are a reason to panic in a menu.
        for body in ["", "not json", "{\"enabled\":true}", "{\"enabled\":\"yes\"}"] {
            assert_eq!(parse_log_location(body), LogLocation::Disabled, "{body:?}");
        }
    }

    #[test]
    fn the_logs_url_points_at_the_core() {
        assert_eq!(logs_url(8123), "http://127.0.0.1:8123/logs");
    }
}
