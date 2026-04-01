APP_NAME := VoiceFlow
BUILD_DIR := .build/release
APP_BUNDLE := $(APP_NAME).app
INSTALL_DIR := $(HOME)/Applications
SIGN_IDENTITY := VoiceFlow Dev

.PHONY: build bundle sign install clean test

build:
	swift build -c release

bundle: build
	rm -rf $(APP_BUNDLE)
	mkdir -p $(APP_BUNDLE)/Contents/MacOS
	mkdir -p $(APP_BUNDLE)/Contents/Resources
	cp $(BUILD_DIR)/$(APP_NAME) $(APP_BUNDLE)/Contents/MacOS/$(APP_NAME)
	cp Info.plist $(APP_BUNDLE)/Contents/Info.plist

sign: bundle
	codesign --force --sign "$(SIGN_IDENTITY)" $(APP_BUNDLE)

install: sign
	mkdir -p $(INSTALL_DIR)
	rm -rf $(INSTALL_DIR)/$(APP_BUNDLE)
	cp -R $(APP_BUNDLE) $(INSTALL_DIR)/$(APP_BUNDLE)
	@echo ""
	@echo "Installed to $(INSTALL_DIR)/$(APP_BUNDLE)"
	@echo "  Launch: open $(INSTALL_DIR)/$(APP_BUNDLE)"
	@echo ""
	@echo "  First install only: System Settings > Privacy & Security > Accessibility > add VoiceFlow"

test:
	swift test

clean:
	swift package clean
	rm -rf $(APP_BUNDLE)
