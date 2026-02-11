# ZMK Corne TP Makefile
# Updates keymap image locally; firmware builds via GitHub Actions on push

.PHONY: all keymap-img clean help

# Paths
VENV := .venv
KEYMAP_IMG_DIR := keymap_img

all: keymap-img

# Update keymap image
keymap-img:
	@echo "Updating keymap image..."
	@cd $(KEYMAP_IMG_DIR) && PATH="$(CURDIR)/$(VENV)/bin:$$PATH" ./update_keymap_img.sh
	@echo "Keymap image updated: $(KEYMAP_IMG_DIR)/keymap.svg"

# Clean build artifacts
clean:
	rm -f $(KEYMAP_IMG_DIR)/keymap.yaml $(KEYMAP_IMG_DIR)/keymap.svg

help:
	@echo "Available targets:"
	@echo "  all        - Update keymap image (default)"
	@echo "  keymap-img - Update keymap SVG image"
	@echo "  clean      - Remove generated files"
	@echo "  help       - Show this help"
	@echo ""
	@echo "Note: Firmware builds via GitHub Actions when you push to the repo."
