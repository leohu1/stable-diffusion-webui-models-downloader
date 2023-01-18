import launch

if not launch.is_installed("wget"):
    launch.run_pip("install wget", "requirements for models_downloader")