# ZMK Corne TP Makefile
# Updates keymap image locally; firmware builds via GitHub Actions on push

.PHONY: all keymap-img clean help setup venv validate

# Paths
VENV := .venv
KEYMAP_IMG_DIR := keymap_img
KEYMAP_FILE := config/corne_tp.keymap
PYTHON := python3

all: keymap-img

# Set up venv and install dependencies
setup: venv
	@echo "Setup complete. Run 'make' to generate keymap image."

venv: $(VENV)/bin/keymap

$(VENV)/bin/keymap:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV)
	@echo "Installing keymap-drawer..."
	$(VENV)/bin/pip install --upgrade pip
	$(VENV)/bin/pip install keymap-drawer

# Validate keymap keycodes
validate:
	@echo "Validating keymap keycodes..."
	@$(PYTHON) scripts/validate_keymap.py $(KEYMAP_FILE)

# Update keymap image
keymap-img: $(VENV)/bin/keymap
	@echo "Updating keymap image..."
	@cd $(KEYMAP_IMG_DIR) && PATH="$(CURDIR)/$(VENV)/bin:$$PATH" ./update_keymap_img.sh
	@echo "Keymap image updated: $(KEYMAP_IMG_DIR)/keymap.svg"

# Clean build artifacts
clean:
	rm -f $(KEYMAP_IMG_DIR)/keymap.yaml $(KEYMAP_IMG_DIR)/keymap.svg

# Clean everything including venv
clean-all: clean
	rm -rf $(VENV)

help:
	@echo "Available targets:"
	@echo "  all        - Update keymap image (default)"
	@echo "  setup      - Create venv and install dependencies"
	@echo "  validate   - Check keymap for syntax errors"
	@echo "  keymap-img - Update keymap SVG image"
	@echo "  clean      - Remove generated files"
	@echo "  clean-all  - Remove generated files and venv"
	@echo "  help       - Show this help"
	@echo ""
	@echo "Note: Firmware builds via GitHub Actions when you push to the repo."
