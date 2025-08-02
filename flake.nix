{
  description = "My PyQt5 + Xlib + keyboard dev shell";

  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-25.05";
    flake-utils.url = "github:numtide/flake-utils";
  };

  outputs =
    { nixpkgs, flake-utils, ... }:
    flake-utils.lib.eachDefaultSystem (
      system:
      let
        pkgs = import nixpkgs { inherit system; };
      in
      {
        devShells.default = pkgs.mkShell {
          buildInputs = with pkgs; [
            (python3.withPackages (
              ps: with ps; [
                pyqt5
                xlib
                keyboard
              ]
            ))
            wmctrl
            kdotool
            maim
            qt5.qtbase
            qt5.qtwayland
            qt5.qtimageformats
          ];

          shellHook = ''
            # Set up Qt plugin paths properly
            export QT_PLUGIN_PATH="${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins:${pkgs.qt5.qtimageformats}/lib/qt-${pkgs.qt5.qtbase.version}/plugins"
            # export QT_QPA_PLATFORM_PLUGIN_PATH="${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/platforms"

            # X11/xlib specific environment variables for window management
            export QT_QPA_PLATFORM="xcb"
            export XDG_SESSION_TYPE="x11"

            # Ensure proper X11 display and authorization
            export DISPLAY="''${DISPLAY:-:0}"

            # For better window manager integration
            export QT_AUTO_SCREEN_SCALE_FACTOR=0
            export QT_SCREEN_SCALE_FACTORS=""

            echo "🛠️  Dev-shell ready!"
            echo "🖼️  Qt plugin path: $QT_PLUGIN_PATH"
            echo "🖼️  Platform plugins: $QT_QPA_PLATFORM_PLUGIN_PATH"
            echo "🖥️  Qt platform: $QT_QPA_PLATFORM"
            echo "🪟  Display: $DISPLAY"

            # List available image format plugins
            echo "📷 Available image format plugins:"
            echo "   From qtbase:"
            ls -la ${pkgs.qt5.qtbase}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/imageformats/ 2>/dev/null || echo "   qtbase imageformats not found"
            echo "   From qtimageformats:"
            ls -la ${pkgs.qt5.qtimageformats}/lib/qt-${pkgs.qt5.qtbase.version}/plugins/imageformats/ 2>/dev/null || echo "   qtimageformats not found"
          '';
        };
      }
    );
}
