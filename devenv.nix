{
  pkgs,
  lib,
  config,
  inputs,
  ...
}:
let
  pkgs-unstable = import inputs.nixpkgs-unstable { system = pkgs.stdenv.system; };
  pythonInterpreter = config.languages.python.package.interpreter;
  venvPath = "${config.env.DEVENV_STATE}/venv";
in
{
  packages = with pkgs-unstable; [
    git
  ];

  enterShell = ''
    echo "buvar_aiohttp devenv ready: $(python --version)"
  '';

  # https://devenv.sh/tests/
  enterTest = ''
    echo "Running tests"
  '';

  # Rebuild the uv-managed venv when the Python interpreter changes.
  # The stock devenv:python:virtualenv task is disabled when uv.sync is on,
  # so a stale venv (built against an older interpreter) is otherwise reused
  # and crashes (e.g. GLIBC_ABI_GNU2_TLS not found).
  tasks."local:python:venv-guard" = {
    description = "Rebuild venv if the Python interpreter changed";
    exec = ''
      set -eu
      if [ -d "${venvPath}" ]; then
        have="$(${pkgs.coreutils}/bin/readlink -f "${venvPath}/bin/python3" 2>/dev/null || true)"
        want="$(${pkgs.coreutils}/bin/readlink -f "${pythonInterpreter}" 2>/dev/null || true)"
        if [ -z "$have" ] || [ "$have" != "$want" ]; then
          echo "Python interpreter changed (have='$have' want='$want'); rebuilding venv"
          ${pkgs.coreutils}/bin/rm -rf "${venvPath}"
        fi
      fi
    '';
    before = [ "devenv:python:uv" ];
    showOutput = true;
  };

  # https://devenv.sh/services/
  # services.postgres.enable = true;

  # https://devenv.sh/languages/
  languages.python = {
    enable = true;
    version = "3.13";
    uv = {
      enable = true;
      sync.enable = true;
    };
    venv = {
      enable = true;
    };
  };
}
