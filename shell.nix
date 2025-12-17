let
  nixconfig = builtins.getFlake "github:death916/nixconfig";
  unstable = nixconfig.inputs.nixpkgs-unstable.legacyPackages.x86_64-linux;
  pkgs = nixconfig.inputs.nixpkgs.legacyPackages.x86_64-linux;
in
pkgs.mkShell {
  packages = with pkgs; [
    python313Packages.uv
    python313Packages.ninja
    python313Packages.numpy
    bun

  ];
  shellHook = ''
    source .venv/bin/activate
    # export PATH="${pkgs.bun}/bin:$PATH"
    # export BUN_INSTALL="${pkgs.bun}/bin/bun"
    export REFLEX_USE_SYSTEM_BUN=True
    echo venv activated and bun version set
  '';
}
