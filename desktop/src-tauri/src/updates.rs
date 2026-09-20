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
    match ureq::get(&updates_url(port))
        .timeout(REQUEST_TIMEOUT)
        .call()
    {
        Ok(response) => parse_update_answer(&response.into_string().unwrap_or_default()),
        Err(err) => UpdateAnswer::Unknown {
            reason: format!("the core could not be reached ({err})"),
        },
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
