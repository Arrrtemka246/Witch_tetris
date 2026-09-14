#---------------------------------------------------------------------------------
.SUFFIXES:
#---------------------------------------------------------------------------------

ifeq ($(strip $(DEVKITARM)),)
$(error "Please set DEVKITARM in your environment. Install devkitPro/devkitARM + 3ds-dev.")
endif

TOPDIR ?= $(CURDIR)
include $(DEVKITARM)/3ds_rules

TARGET          := witch_tetris_3ds
BUILD           := build
SOURCES         := source
INCLUDES        := include
ROMFS           := romfs
ASSET_PROFILE   ?= core

APP_TITLE       := W.I.T.C.H. Tetris 3DS
APP_DESCRIPTION := Native Nintendo 3DS port
APP_AUTHOR      := Arrrtemka246

# CIA identity. Keep UNIQUE_ID stable: changing it would create another HOME Menu title.
APP_UNIQUE_ID   := 0x57C17
APP_PRODUCT_CODE:= CTR-H-WT3D
CIA_RSF         := cia/app.rsf
CIA_ICON_PNG    := cia/icon.png
CIA_BANNER_PNG  := cia/banner.png
CIA_BANNER_WAV  := cia/banner.wav
CIA_ICON        := $(BUILD)/cia_icon.icn
CIA_BANNER      := $(BUILD)/cia_banner.bnr

ARCH        := -march=armv6k -mtune=mpcore -mfloat-abi=hard -mtp=soft

CFLAGS      := -g -Wall -Wextra -O2 -mword-relocations \
               -ffunction-sections \
               $(ARCH)
CFLAGS      += $(INCLUDE) -D__3DS__

CXXFLAGS    := $(CFLAGS) -fno-rtti -fno-exceptions -std=gnu++11
ASFLAGS     := -g $(ARCH)
LDFLAGS     := -specs=3dsx.specs -g $(ARCH) -Wl,-Map,$(notdir $*.map)

LIBS        := -lmpg123 -lcitro2d -lcitro3d -lctru -lm
LIBDIRS     := $(CTRULIB)

ifneq ($(BUILD),$(notdir $(CURDIR)))

export OUTPUT    := $(CURDIR)/$(TARGET)
export TOPDIR    := $(CURDIR)
export VPATH     := $(foreach dir,$(SOURCES),$(CURDIR)/$(dir))
export DEPSDIR   := $(CURDIR)/$(BUILD)

CFILES      := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.c)))
CPPFILES    := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.cpp)))
SFILES      := $(foreach dir,$(SOURCES),$(notdir $(wildcard $(dir)/*.s)))

ifeq ($(strip $(CPPFILES)),)
export LD := $(CC)
else
export LD := $(CXX)
endif

export OFILES_SOURCES := $(CPPFILES:.cpp=.o) $(CFILES:.c=.o) $(SFILES:.s=.o)
export OFILES         := $(OFILES_SOURCES)

export INCLUDE := $(foreach dir,$(INCLUDES),-I$(CURDIR)/$(dir)) \
                  $(foreach dir,$(LIBDIRS),-I$(dir)/include) \
                  -I$(PORTLIBS)/include \
                  -I$(CURDIR)/$(BUILD)

export LIBPATHS := $(foreach dir,$(LIBDIRS),-L$(dir)/lib) -L$(PORTLIBS)/lib
export _3DSXDEPS := $(if $(NO_SMDH),,$(OUTPUT).smdh)

ifeq ($(strip $(NO_SMDH)),)
export _3DSXFLAGS += --smdh=$(CURDIR)/$(TARGET).smdh
endif
export _3DSXFLAGS += --romfs=$(CURDIR)/$(ROMFS)

.PHONY: all clean assets full-assets cia cia-meta

all: assets
	@mkdir -p $(BUILD)
	@$(MAKE) --no-print-directory -C $(BUILD) -f $(CURDIR)/Makefile

assets:
	@python3 tools/prepare_assets.py --profile $(ASSET_PROFILE)

full-assets:
	@python3 tools/prepare_assets.py --profile full

cia-meta:
	@mkdir -p $(BUILD) cia
	@python3 tools/prepare_cia_meta.py
	@bannertool makesmdh \
		-s "$(APP_TITLE)" \
		-l "$(APP_DESCRIPTION)" \
		-p "$(APP_AUTHOR)" \
		-i "$(CIA_ICON_PNG)" \
		-f visible,allow3d,nosavebackups \
		-o "$(CIA_ICON)"
	@bannertool makebanner \
		-i "$(CIA_BANNER_PNG)" \
		-a "$(CIA_BANNER_WAV)" \
		-o "$(CIA_BANNER)"

# Installable HOME Menu build for Luma3DS/FBI.
cia: all cia-meta
	@command -v makerom >/dev/null || (echo "makerom not found" && false)
	@makerom -f cia \
		-o "$(TARGET).cia" \
		-target t \
		-exefslogo \
		-elf "$(TARGET).elf" \
		-rsf "$(CIA_RSF)" \
		-icon "$(CIA_ICON)" \
		-banner "$(CIA_BANNER)" \
		-DAPP_TITLE="$(APP_TITLE)" \
		-DAPP_PRODUCT_CODE="$(APP_PRODUCT_CODE)" \
		-DAPP_UNIQUE_ID="$(APP_UNIQUE_ID)" \
		-DAPP_ROMFS="$(CURDIR)/$(ROMFS)"
	@echo "built ... $(TARGET).cia"

clean:
	@echo clean ...
	@rm -fr $(BUILD) $(ROMFS) .asset_build \
		$(TARGET).3dsx $(TARGET).smdh $(TARGET).elf $(TARGET).map $(TARGET).cia \
		$(CIA_ICON_PNG) $(CIA_BANNER_PNG) $(CIA_BANNER_WAV)

else

$(OUTPUT).3dsx: $(OUTPUT).elf $(_3DSXDEPS)

$(OUTPUT).elf: $(OFILES)

-include $(DEPSDIR)/*.d

endif
