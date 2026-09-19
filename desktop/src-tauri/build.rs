fn main() {
    // The repo root, baked in at compile time so the shell and its tests can
    // find server/.venv without runtime path hunting.
    let manifest = std::env::var("CARGO_MANIFEST_DIR").expect("CARGO_MANIFEST_DIR is always set");
    let repo_root = std::path::Path::new(&manifest)
        .parent()
        .and_then(|p| p.parent())
        .map(|p| p.to_path_buf())
        .expect("src-tauri sits at <repo>/desktop/src-tauri");
    println!("cargo:rustc-env=REPO_ROOT={}", repo_root.display());
    tauri_build::build();
}
