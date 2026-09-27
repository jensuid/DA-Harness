//! Opening the LLM settings panel from the menu bar (W2X-012 phase B).
//!
//! Phase A made the degradation a stated one: the core answers `/llm/status`
//! and the banner says what the analyst is actually getting. Phase B is the
//! half that changes it - a packaged app cannot read a `.env` that was never
//! bundled, so the credential reaches the core as a file the settings surface
//! writes into the data directory the shell already pointed at.
//!
//! This module is the menu item's half, and it deliberately adds no capability.
//! The panel the analyst fills in is the bundle's own surface - the same one
//! `updates.rs` reaches with an evaluated script, because that channel already
//! exists and needs no ACL entry (`core:default` grants no commands; the webview
//! posts to the core over plain HTTP, which it already does for everything
//! else). A native window would mean a Tauri command and a permission set that
//! was kept empty on purpose.
//!
//! Everything degrades to a sentence rather than an error, for the same reason
//! `logs.rs` does: a core that is still booting cannot have settings yet, and
//! a menu item that fails when the analyst needs it most is worse than one
//! that says so.

use std::time::Duration;

use crate::core_server::PORT;

/// Per-request cap so a hung core cannot freeze the menu.
const REQUEST_TIMEOUT: Duration = Duration::from_secs(2);

/// The custom event name the bundle's settings layer listens for
/// (`web/src/shell.ts`). The panel is the bundle's own surface; this event is
/// only ever the shell telling it to open, never the settings themselves - the
/// panel fetches and writes those over HTTP, so nothing trust-bearing rides
/// this channel.
const SETTINGS_EVENT: &str = "dah-settings";

/// Where the core answers whether the LLM is configured.
pub fn status_url(port: u16) -> String {
    format!("http://127.0.0.1:{port}/llm/status")
}

/// Read `configured` out of the core's answer, tolerating anything.
///
/// `false` is the safe default of a body the shell cannot interpret, for the
/// same reason `parse_update_answer` lands on `Unknown`: a menu item must
/// never panic on a body it does not recognise, and a core that is still
/// booting or predates the field answers nothing the shell can read.
pub fn parse_configured(body: &str) -> bool {
    let Ok(value) = serde_json::from_str::<serde_json::Value>(body) else {
        return false;
    };
    value.get("configured").and_then(|v| v.as_bool()) == Some(true)
}

/// Ask the running core whether the LLM is configured, so the menu item can
/// say the state instead of opening a panel the analyst has no reason to look
/// at. A transport failure is `false`: during boot the core is not answering
/// yet, and a core older than this endpoint 404s. Both are the same thing from
/// a menu's point of view - not configured.
pub fn llm_configured(port: u16) -> bool {
    match ureq::get(&status_url(port)).timeout(REQUEST_TIMEOUT).call() {
        Ok(response) if response.status() == 200 => {
            parse_configured(&response.into_string().unwrap_or_default())
        }
        _ => false,
    }
}

/// The JavaScript the shell evaluates in its own webview to open the panel.
pub fn open_script() -> String {
    format!("window.dispatchEvent(new CustomEvent('{SETTINGS_EVENT}'))")
}

#[cfg(test)]
mod tests {
    use super::*;

    /// The event name is the one thing the Rust side and the TypeScript side
    /// must agree on, and nothing else in the codebase checks it - a rename in
    /// the bundle would make the menu item a no-op, which is the defect this
    /// module exists to avoid. Mirrors the guard `updates.rs` keeps on
    /// `dah-notice`.
    #[test]
    fn the_script_dispatches_the_event_the_bundle_listens_for() {
        let source = include_str!("../../../web/src/shell.ts");
        assert!(
            source.contains(&format!("'{SETTINGS_EVENT}'")),
            "web/src/shell.ts no longer listens on the event open_script emits"
        );
        assert!(open_script().contains(SETTINGS_EVENT));
    }

    #[test]
    fn a_configured_answer_reads_true() {
        assert!(parse_configured(
            r#"{"configured":true,"provider":"DAH_LLM_API_KEY","model":"m","base_url":"https://e/v1"}"#
        ));
    }

    #[test]
    fn an_unconfigured_answer_reads_false() {
        assert!(!parse_configured(
            r#"{"configured":false,"provider":null,"model":"gpt-4o-mini","base_url":"https://api.openai.com/v1"}"#
        ));
    }

    #[test]
    fn a_body_the_shell_does_not_recognise_reads_false() {
        // A core that grew a different response, a gateway's HTML error page,
        // an empty buffer - none of them are a reason to panic in a menu, and
        // none of them mean the LLM is there.
        for body in [
            "",
            "not json",
            r#"{"configured":"yes"}"#,
            r#"{"configured":null}"#,
        ] {
            assert!(!parse_configured(body), "{body:?}");
        }
    }

    #[test]
    fn the_url_points_at_the_core() {
        assert_eq!(status_url(PORT), "http://127.0.0.1:8123/llm/status");
    }
}
