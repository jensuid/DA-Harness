//! Telling a user a newer build exists (P6-UPDATE-005).
//!
//! The release pipeline publishes a build per tag, but an installed app had no
//! way to learn that. This module is the shell's half of the check: it asks the
//! core - which alone has the network egress and the version - and then either
//! puts the download in front of the user or says why it could not tell.
//!
//! Everything degrades to a sentence rather than an error, for the same reason
//! `logs.rs` does: the repository is private, so an unauthenticated release-feed
//! request legitimately answers 404, and a menu item that reports "could not
//! check - the repository may be private" is honest where one that silently
//! claims "you are up to date" would be a lie the user cannot inspect. The app
//! is also unsigned (DEC-006), so a self-replacing updater cannot verify a
//! payload; the check is what ships, and `tauri-plugin-updater` slots in when
//! signing does.

use std::process::Command;
use std::time::Duration;

/// Per-request cap so a hung core cannot freeze the menu.
const REQUEST_TIMEOUT: Duration = Duration::from_secs(15);

/// The running core's port - the same one every host agrees on.
use crate::core_server::PORT;

/// What `GET /updates/latest` told us, as a menu can show it.
#[derive(Debug, Clone, PartialEq, Eq)]
pub enum UpdateAnswer {
    /// A newer build exists; this is its release page.
    Available {
        current: String,
        latest: String,
        page_url: String,
    },
    /// The feed was reached and nothing newer exists.
    Current { current: String, latest: String },
    /// The feed could not tell us. `reason` is the sentence to show a user:
    /// "the release feed is not reachable; the repository may be private".
    Unknown { reason: String },
}

/// Where the core answers for its own update check.
pub fn updates_url(port: u16) -> String {
    format!("http://127.0.0.1:{port}/updates/latest")
}

/// The one-line summary a menu item's text can carry.
pub fn update_summary(answer: &UpdateAnswer) -> String {
    match answer {
        UpdateAnswer::Available { latest, .. } => {
            format!("DAH {latest} is available - download it")
        }
        UpdateAnswer::Current { latest, .. } => {
            format!("DAH {latest} is the latest build")
        }
        UpdateAnswer::Unknown { reason } => format!("Could not check: {reason}"),
    }
}

/// Read the answer out of the core's JSON, tolerating anything.
///
/// A status that is not one of the three known values, a missing field or a
/// body that is not JSON at all is `Unknown` - a menu must never panic on a
/// body it does not recognise, and "could not tell" is the truthful reading of
/// a body the shell cannot interpret.
pub fn parse_update_answer(body: &str) -> UpdateAnswer {
    let Ok(value) = serde_json::from_str::<serde_json::Value>(body) else {
        return UpdateAnswer::Unknown {
            reason: "the core sent a body this build does not recognise".to_string(),
        };
    };
    let status = value.get("status").and_then(|v| v.as_str()).unwrap_or("");
    let current = value
        .get("current")
        .and_then(|v| v.as_str())
        .unwrap_or("unknown")
        .to_string();
    match status {
        "available" => {
            let latest = value.get("latest").and_then(|v| v.as_str()).unwrap_or("");
            let page_url = value.get("page_url").and_then(|v| v.as_str()).unwrap_or("");
            // Without a page there is nothing to open, which is itself a
            // state to report rather than a link to guess at.
            if latest.is_empty() || page_url.is_empty() {
                return UpdateAnswer::Unknown {
                    reason: "the core named a newer build but no download page".to_string(),
                };
            }
            UpdateAnswer::Available {
                current,
                latest: latest.to_string(),
                page_url: page_url.to_string(),
            }
        }
        "current" => UpdateAnswer::Current {
            current,
            latest: value
                .get("latest")
                .and_then(|v| v.as_str())
                .unwrap_or("unknown")
                .to_string(),
        },
        _ => UpdateAnswer::Unknown {
            reason: value
                .get("reason")
                .and_then(|v| v.as_str())
                .unwrap_or("the core could not determine the latest build")
                .to_string(),
        },
    }
}

/// Ask the core whether a newer build exists.
///
/// Any transport failure is `Unknown`: during boot the core is not answering
/// yet, and a core older than this endpoint 404s. Both are the same thing from
/// a menu's point of view - nothing to show but a sentence.
pub fn check_for_update(port: u16) -> UpdateAnswer {
    check_for_update_with_body(port).0
}

/// Ask the core, and keep the body it answered with.
///
/// The parsed answer is what the log line summarises; the body is what the
/// window needs, because the vocabulary the notice renders is the core's own
/// - the shell hands the whole body to the bundle rather than rewording it,
/// which keeps `unknown`'s reason from becoming a silent "up to date" (the
/// exact lie P6-UPDATE-005 built this check to avoid). A transport failure
/// carries no body, and the shell reports that to the window in its own
/// sentence instead of dropping the event.
pub fn check_for_update_with_body(port: u16) -> (UpdateAnswer, Option<String>) {
    match ureq::get(&updates_url(port))
        .timeout(REQUEST_TIMEOUT)
        .call()
    {
        Ok(response) => {
            let body = response.into_string().unwrap_or_default();
            (parse_update_answer(&body), Some(body))
        }
        Err(err) => (
            UpdateAnswer::Unknown {
                reason: format!("the core could not be reached ({err})"),
            },
            None,
        ),
    }
}

/// Open a URL in the user's browser, the way the reveal-logs menu opens
/// Finder - through `open`, so the shell gains no crate and no new privilege.
///
/// Returns the URL on success so a caller can report what it opened.
pub fn open_in_browser(url: &str) -> Result<String, String> {
    Command::new("open")
        .arg(url)
        .spawn()
        .map_err(|err| format!("could not open the browser: {err}"))?;
    Ok(url.to_string())
}

/// The custom event name the bundle's notice layer listens for
/// (`web/src/shell.ts`).
///
/// FIX-UPDATES-009 (W-005): the shell had the check and the log line and no
/// delivery, so on a private repository - where the feed always answers 404 -
/// the item was permanently, silently dead. The delivery is the bundle's own
/// surface because that is the one the window already has: the shell gains no
/// dependency (DEC-001), and `tauri-plugin-dialog` on Tauri 2 is a
/// network-fetched plugin the offline app cannot install.
const NOTICE_EVENT: &str = "dah-notice";

/// The JavaScript the shell evaluates in its own webview to hand the answer to
/// the bundle.
///
/// `body` is the core's own JSON when the transport kept a body that is
/// actually JSON, and `None` otherwise - the shell then rebuilds the body from
/// the parsed answer. Both halves matter: a body that is not JSON cannot be
/// embedded in the script, because the eval would throw a `SyntaxError` and the
/// menu item would be silent a second time, and a shell-rebuilt body still
/// carries the core's own vocabulary rather than a sentence the shell reworded
/// - so an unreachable feed stays "could not tell" rather than becoming a
/// silent "up to date", the lie P6-UPDATE-005 built this check to avoid.
/// `describeUpdate` in the bundle mirrors `update_summary` here, so the window
/// and the log line always say the same thing about the same answer.
pub fn notice_script(answer: &UpdateAnswer, body: Option<&str>) -> String {
    let payload = body
        .filter(|raw| serde_json::from_str::<serde_json::Value>(raw).is_ok())
        .map(str::to_string)
        .unwrap_or_else(|| answer.to_json_string());
    format!("window.dispatchEvent(new CustomEvent('{NOTICE_EVENT}',{{detail:{payload}}}))")
}

impl UpdateAnswer {
    /// The core's own body shape, for the case the transport kept no body.
    fn to_json_string(&self) -> String {
        match self {
            UpdateAnswer::Available { current, latest, page_url } => format!(
                r#"{{"status":"available","current":{},"latest":{},"page_url":{}}}"#,
                json_string(current),
                json_string(latest),
                json_string(page_url),
            ),
            UpdateAnswer::Current { current, latest } => format!(
                r#"{{"status":"current","current":{},"latest":{}}}"#,
                json_string(current),
                json_string(latest),
            ),
            UpdateAnswer::Unknown { reason } => format!(
                r#"{{"status":"unknown","current":"unknown","reason":{}}}"#,
                json_string(reason),
            ),
        }
    }
}

/// A quoted JSON string. The values come from the shell's own parsed answer,
/// never from the analyst, so a quote inside one is escaped rather than
/// trusted.
fn json_string(value: &str) -> String {
    let mut out = String::with_capacity(value.len() + 2);
    out.push('"');
    for ch in value.chars() {
        match ch {
            '"' => out.push_str(r#"\""#),
            '\\' => out.push_str(r"\\"),
            '\n' => out.push_str(r"\n"),
            '\r' => out.push_str(r"\r"),
            '\t' => out.push_str(r"\t"),
            _ => out.push(ch),
        }
    }
    out.push('"');
    out
}

/// Deliver the check's answer to the window the menu item was pulled from.
///
/// Returns the sentence that was delivered (for the log) or the reason the
/// delivery failed (also for the log) - the caller still writes both, because
/// a delivery that silently replaced the log line would hide the answer from
/// the one place it always reached.
pub fn deliver_update_notice(
    window: &tauri::WebviewWindow,
    answer: &UpdateAnswer,
    body: Option<&str>,
) -> Result<String, String> {
    let script = notice_script(answer, body);
    window
        .eval(&script)
        // The script is the shell's own string, built from the core's JSON;
        // a failure here is the webview's, and it names itself rather than the
        // answer the analyst is still waiting on.
        .map_err(|err| format!("could not reach the window with the update answer: {err}"))?;
    Ok(update_summary(answer))
}

#[cfg(test)]
mod notice_tests {
    use super::*;

    /// The event name is the one thing the Rust side and the TypeScript side
    /// must agree on, and nothing else in the codebase checks it - a rename in
    /// the bundle would make the menu item silent again, which is the exact
    /// defect this task closes.
    #[test]
    fn the_script_dispatches_the_event_the_bundle_listens_for() {
        let source = include_str!("../../../web/src/shell.ts");
        assert!(
            source.contains(&format!("'{NOTICE_EVENT}'")),
            "web/src/shell.ts no longer listens on the event notice_script emits"
        );
    }

    #[test]
    fn the_script_carries_the_core_body_unmodified() {
        let script = notice_script(
            &UpdateAnswer::Unknown { reason: "because".to_string() },
            Some(r#"{"status":"unknown","reason":"because"}"#),
        );
        assert!(script.contains("dah-notice"));
        // The body rides along as the event's detail, so the vocabulary the
        // window shows is the core's own.
        assert!(script.contains(r#""status":"unknown""#));
        assert!(script.contains(r#""reason":"because""#));
    }

    /// An answer whose body never arrived - the core would not answer, or
    /// answered something the transport could not read - still reaches the
    /// window. The shell builds the body itself from the parsed answer, so the
    /// notice the analyst sees is the same sentence the log line wrote.
    #[test]
    fn an_answer_without_a_body_still_reaches_the_window() {
        let script = notice_script(
            &UpdateAnswer::Unknown { reason: "the core could not be reached".to_string() },
            None,
        );
        assert!(script.contains("dah-notice"));
        assert!(script.contains(r#""status":"unknown""#));
        assert!(script.contains("the core could not be reached"));
    }

    /// A body the shell cannot parse still dispatches: the eval is built from
    /// the parsed answer, so an unparseable body becomes the parsed `Unknown`
    /// rather than a JavaScript syntax error that would have made the menu
    /// item silent a second time.
    #[test]
    fn an_unparseable_body_still_dispatches() {
        let script = notice_script(
            &parse_update_answer("<html>not json</html>"),
            Some("<html>not json</html>"),
        );
        assert!(script.contains("dah-notice"));
        assert!(script.contains(r#""status":"unknown""#));
        // The layer's describeUpdate degrades the rest.
    }

    #[test]
    fn an_available_build_carries_its_page_and_opens() {
        let answer = UpdateAnswer::Available {
            current: "0.1.0".to_string(),
            latest: "v0.2.0".to_string(),
            page_url: "https://example.test/v0.2.0".to_string(),
        };
        let script = notice_script(
            &answer,
            Some(r#"{"status":"available","current":"0.1.0","latest":"v0.2.0","page_url":"https://example.test/v0.2.0"}"#),
        );
        assert!(script.contains("dah-notice"));
        assert!(script.contains(r#""status":"available""#));
        // The delivery names the download page; the browser still opens it.
        assert_eq!(
            update_summary(&answer),
            "DAH v0.2.0 is available - download it"
        );
    }

    #[test]
    fn a_current_build_reaches_the_window_too() {
        let script = notice_script(
            &UpdateAnswer::Current { current: "0.1.0".to_string(), latest: "v0.1.0".to_string() },
            Some(r#"{"status":"current","current":"0.1.0","latest":"v0.1.0"}"#),
        );
        assert!(script.contains(r#""status":"current""#));
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn a_newer_build_carries_its_page() {
        let answer = parse_update_answer(
            r#"{"status":"available","current":"0.1.0","latest":"v0.2.0",
                "page_url":"https://github.com/jensuid/DA-Harness/releases/tag/v0.2.0",
                "notes":"fixes"}"#,
        );
        assert_eq!(
            answer,
            UpdateAnswer::Available {
                current: "0.1.0".to_string(),
                latest: "v0.2.0".to_string(),
                page_url: "https://github.com/jensuid/DA-Harness/releases/tag/v0.2.0"
                    .to_string(),
            }
        );
        assert!(update_summary(&answer).contains("v0.2.0"));
    }

    #[test]
    fn an_equal_build_is_current() {
        let answer = parse_update_answer(
            r#"{"status":"current","current":"0.1.0","latest":"v0.1.0"}"#,
        );
        assert_eq!(
            answer,
            UpdateAnswer::Current {
                current: "0.1.0".to_string(),
                latest: "v0.1.0".to_string(),
            }
        );
        assert!(update_summary(&answer).contains("latest"));
    }

    #[test]
    fn a_private_repository_is_unknown_with_a_reason() {
        let answer = parse_update_answer(
            r#"{"status":"unknown","current":"0.1.0",
                "reason":"the release feed is not reachable; the repository may be private"}"#,
        );
        assert!(matches!(answer, UpdateAnswer::Unknown { .. }));
        assert!(update_summary(&answer).contains("private"));
    }

    #[test]
    fn an_unknown_status_without_a_reason_still_has_one() {
        let answer = parse_update_answer(r#"{"status":"unknown"}"#);
        assert!(matches!(answer, UpdateAnswer::Unknown { ref reason } if !reason.is_empty()));
    }

    #[test]
    fn a_newer_build_without_a_page_is_unknown_not_a_guess() {
        let answer = parse_update_answer(
            r#"{"status":"available","current":"0.1.0","latest":"v0.2.0"}"#,
        );
        // There is nothing to open, and the shell will not fabricate a URL.
        assert!(matches!(answer, UpdateAnswer::Unknown { .. }));
    }

    #[test]
    fn an_unrecognised_status_is_unknown() {
        let answer = parse_update_answer(r#"{"status":"whatever","current":"0.1.0"}"#);
        assert!(matches!(answer, UpdateAnswer::Unknown { .. }));
    }

    #[test]
    fn a_body_that_is_not_json_is_unknown() {
        let answer = parse_update_answer("<html>not json</html>");
        assert!(matches!(answer, UpdateAnswer::Unknown { .. }));
    }

    #[test]
    fn an_empty_body_is_unknown() {
        let answer = parse_update_answer("");
        assert!(matches!(answer, UpdateAnswer::Unknown { .. }));
    }

    #[test]
    fn a_missing_current_version_reads_as_unknown_rather_than_panicking() {
        let answer = parse_update_answer(r#"{"status":"current"}"#);
        assert!(matches!(answer, UpdateAnswer::Current { .. }));
    }

    #[test]
    fn the_url_is_built_from_the_shared_port() {
        assert!(updates_url(PORT).contains("/updates/latest"));
    }
}
