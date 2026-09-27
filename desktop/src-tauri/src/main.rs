//! DAH desktop shell (roadmap item 10, DEC-001).
//!
//! A host swap, not a rewrite: Tauri serves the same React bundle the browser
//! host serves, and that bundle keeps talking to the same FastAPI core over
//! HTTP. The shell's only jobs are to start that core, wait until it answers,
//! show the window, and stop the core when the user is done.

#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod core_server;
mod logs;
mod settings;
mod updates;

use std::path::PathBuf;
use std::sync::Mutex;

use core_server::{health_url, resolve_server_command, wait_for_health, ServerChild, PORT};
use logs::reveal_core_logs;
use tauri::menu::{Menu, SubmenuBuilder};
use tauri::{Manager, WindowEvent};
use updates::{
    check_for_update_with_body, deliver_update_notice, open_in_browser, update_summary,
    UpdateAnswer,
};

/// The menu items' ids; the event handler matches on these.
const REVEAL_LOGS_ID: &str = "reveal_logs";
const CHECK_UPDATES_ID: &str = "check_updates";
const SETTINGS_ID: &str = "llm_settings";

fn main() {
    let app = tauri::Builder::default()
        // The running core lives as long as the app does.
        .manage(Mutex::new(None::<ServerChild>))
        .on_menu_event(|app, event| {
            // The one menu item DAH adds. Everything else in the bar is a
            // standard macOS item the builder pulls in.
            if event.id().as_ref() == REVEAL_LOGS_ID {
                match reveal_core_logs(PORT) {
                    logs::RevealOutcome::Revealed(path) => eprintln!(
                        "DAH shell: revealed the core's log at {}",
                        path.display()
                    ),
                    logs::RevealOutcome::Disabled => eprintln!(
                        "DAH shell: the core reported file logging is off, so                          there is no log to reveal"
                    ),
                    logs::RevealOutcome::Unreachable => eprintln!(
                        "DAH shell: could not reach the core to find its log;                          it may still be starting"
                    ),
                }
                let _ = app;
            } else if event.id().as_ref() == SETTINGS_ID {
                // The panel is the bundle's own surface, so this is a single
                // eval - the same channel `updates.rs` uses, and one that
                // needs no capability (`core:default` grants no commands). The
                // panel fetches and writes the settings itself over the HTTP
                // the bundle already speaks, so nothing trust-bearing rides
                // this event.
                open_settings_panel(app);
            } else if event.id().as_ref() == CHECK_UPDATES_ID {
                // Ask the core, which alone has the network egress and the
                // version, then put the answer in front of the user
                // (FIX-UPDATES-009, W-005). For a private repository the feed
                // is always unreachable, and before this the item's three
                // outcomes reached stderr only - so the menu looked dead while
                // the core was answering honestly.
                let (answer, body) = check_for_update_with_body(PORT);
                eprintln!("DAH shell: {}", update_summary(&answer));
                if let UpdateAnswer::Available { page_url, .. } = &answer {
                    match open_in_browser(page_url) {
                        Ok(url) => eprintln!("DAH shell: opened the release page at {url}"),
                        Err(err) => eprintln!("DAH shell: {err}"),
                    }
                }
                deliver_update_answer(app, &answer, body.as_deref());
            }
        })
        .setup(|app| {
            // macOS gets a real menu bar. The app menu keeps About and Cmd+Q -
            // without them, setting any custom menu takes the standard items
            // away - and Edit keeps the text editing a data tool needs.
            let app_menu = SubmenuBuilder::new(app, "DAH")
                .about(None)
                .separator()
                .text(SETTINGS_ID, "DAH Settings…")
                .separator()
                .text(CHECK_UPDATES_ID, "Check for Updates...")
                .text(REVEAL_LOGS_ID, "Reveal DAH Logs")
                .separator()
                .quit()
                .build()?;
            let edit_menu = SubmenuBuilder::new(app, "Edit")
                .undo()
                .redo()
                .separator()
                .cut()
                .copy()
                .paste()
                .select_all()
                .build()?;
            let menu = Menu::new(app)?;
            menu.append_items(&[&app_menu, &edit_menu])?;
            app.set_menu(menu)?;

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

/// Open the LLM settings panel (W2X-012 phase B).
///
/// The panel is the bundle's own surface - the same channel `updates.rs`
/// reaches, and one that needs no capability - so this is a single evaluated
/// script rather than a native window. A delivery that cannot reach the
/// window is reported to the log rather than swallowed, so the menu item
/// degrades to nothing rather than to silence.
fn open_settings_panel(app: &tauri::AppHandle) {
    let Some(window) = app.get_webview_window("main") else {
        eprintln!("DAH shell: could not open the settings panel - the main window is gone");
        return;
    };
    match window.eval(&settings::open_script()) {
        Ok(()) => eprintln!("DAH shell: opened the LLM settings panel"),
        Err(err) => eprintln!("DAH shell: could not open the settings panel: {err}"),
    }
}

/// Put the update check's answer in front of the user (FIX-UPDATES-009, W-005).
///
/// The menu item is silent no matter which of the core's three statuses it
/// found, so the answer goes to the window the item was pulled from - and to
/// the log first, because the delivery is added rather than substituted: the
/// stderr line is the one place the answer always reached, and a window that
/// replaced it would hide the answer from anyone reading the shell's output.
///
/// A delivery that cannot reach the window is reported to the log rather than
/// swallowed, so the menu item degrades to what it did before instead of to
/// silence without a trace.
fn deliver_update_answer(app: &tauri::AppHandle, answer: &UpdateAnswer, body: Option<&str>) {
    let Some(window) = app.get_webview_window("main") else {
        eprintln!("DAH shell: could not deliver the update answer - the main window is gone");
        return;
    };
    match deliver_update_notice(&window, answer, body) {
        Ok(delivered) => eprintln!("DAH shell: delivered to the window: {delivered}"),
        Err(err) => eprintln!("DAH shell: {err}"),
    }
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
