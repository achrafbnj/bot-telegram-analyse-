use std::process::Command;

fn main() {
    // Run a Python script as part of the build process
    Command::new("python")
        .arg("path/to/your/python/script.py")
        .status()
        .expect("Failed to run Python script");
}
