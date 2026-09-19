//! DAH desktop shell (roadmap item 10, DEC-001).
//!
//! A host swap, not a rewrite: Tauri serves the same React bundle the browser
//! host serves, and that bundle keeps talking to the same FastAPI core over
//! HTTP. The shell's only jobs are to start that core, wait until it answers,
//! show the window, and stop the core when the user is done.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod core_server;

use std::path::PathBuf;
use std::sync::Mutex;

use core_server::{health_url, resolve_server_command, wait_for_health, PORT, ServerChild};
use tauri::{Manager, WindowEvent};

fn main() {
    let app = tauri::Builder::default()
        // The running core lives as long as the app does.
        .manage(Mutex::new(None::<ServerChild>))
        .setup(|app| {
            let data_dir = app.path().app_data_dir()?;
            std::fs::create_dir_all(&data_dir)?;

            // Release: `dah-core` next to this executable. Dev: the project's
            // virtualenv, found from the path build.rs baked in.
            let shell_dir = current_exe_dir()?;
            let repo_root = PathBuf::from(env!("REPO_ROOT"));
            let resolved = resolve_server_command(&shell_dir, &repo_root);

            eprintln!(
                "DAH shell: starting core: {} {:?} (data dir: {})",
                resolved.program.display(),
                resolved.args,
                data_dir.display()
            );

            let child = resolved.to_process(&data_dir).spawn()?;
            *app.state::<Mutex<Option<ServerChild>>>().lock().unwrap() =
                Some(ServerChild::new(child));

            // Stay hidden until the core actually answers. The bundle polls
            // /health itself, but showing an API-less window first is what makes
            // a double-clickable app feel broken.
            let window = app
                .get_webview_window("main")
                .ok_or_else(|| Box::<dyn std::error::Error>::from("the main window is missing from the config"))?;
            if wait_for_health(&health_url(PORT), resolved.health_timeout()) {
                window.show()?;
            } else {
                // Something is wrong with the core. Show the window anyway - the
                // bundle renders its own unreachable state - and say why loudly.
                eprintln!(
                    "DAH shell: the core did not answer {} within {:?}. Check that \
                     server/.venv exists, or bundle the dah-core sidecar.",
                    health_url(PORT),
                    resolved.health_timeout()
                );
                window.show()?;
            }

            Ok(())
        })
        .on_window_event(|window, event| {
            if let WindowEvent::CloseRequested { .. } = event {
                // Closing the window ends the session: stop the core too, so a
                // stopped DAH does not leave a server holding the port.
                stop_core(window.app_handle());
            }
        })
        .build(tauri::generate_context!())
        .expect("error while building the DAH shell");

    app.run(|app_handle, run_event| {
        // Cmd+Q and the other macOS termination paths exit the process from
        // inside the event loop, so `main`'s values are never dropped and a
        // Drop guard alone would leave the core running. ExitRequested is the
        // last thing that runs before that exit.
        if let tauri::RunEvent::ExitRequested { .. } = run_event {
            stop_core(app_handle);
        }
    });
}

/// The directory this executable sits in - where a bundled `dah-core` lives.
fn current_exe_dir() -> Result<PathBuf, Box<dyn std::error::Error>> {
    std::env::current_exe()?
        .parent()
        .map(PathBuf::from)
        .ok_or_else(|| Box::<dyn std::error::Error>::from("current_exe has no parent directory"))
}

/// Stop the core if it is running. Called when the window closes and when the
/// app is asked to exit; whichever fires first takes the core out of the shared
/// state, so the second call finds nothing left to do.
fn stop_core(app_handle: &tauri::AppHandle) {
    let Some(state) = app_handle.try_state::<Mutex<Option<ServerChild>>>() else {
        return;
    };
    let Some(mut child) = state.lock().unwrap().take() else {
        return;
    };
    if let Err(err) = child.kill() {
        eprintln!("DAH shell: could not stop the core: {err}");
    }
}
