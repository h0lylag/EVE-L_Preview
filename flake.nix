{
  description = "My Python + PyQt5 + Xlib + keyboard dev shell";

  inputs = {
    # pin to a fixed Nixpkgs for reproducibility
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    # helper for multi-system Flakes
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    {
      self,
      nixpkgs,
      flake-utils,
      ...
    }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs {
          inherit system;
          # optionally customize overlays, config, etc.
        };
      in
      {
        # this attr path is what `nix develop` will pick up
        devShells.default = pkgs.mkShell {
          # pull in exactly the Python packages you need
          buildInputs = with pkgs.python3Packages; [
            pyqt5
            python-xlib
            keyboard
          ];
          # optional: notify on shell entry
          shellHook = ''
            echo "Python dev shell ready with PyQt5, Xlib & keyboard"
          '';
        };
      }
    );
}
