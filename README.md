# kiln-spoolman

A [Kiln OS](https://github.com/djvalic/kiln-os) plugin for Flashforge AD5X
printers: each IFS slot gets its own [Spoolman](https://github.com/Donkie/Spoolman)
spool, and whichever slot is loaded into the nozzle becomes Spoolman's
active spool. A multicolour print then books each colour's filament to its
own spool.

Needs Kiln OS with plugin API 1.2 or newer (v0.0.5+), which sends the
`ifs:loaded` event this plugin listens to.

## 1. Connect Moonraker to Spoolman

The Spoolman server runs on another machine (a NAS, a Raspberry Pi,
Docker). Add to the printer's `moonraker.conf` (Fluidd: Configuration):

    [spoolman]
    server: http://192.168.1.10:7912
    sync_rate: 5

After a Moonraker restart Fluidd shows a Spoolman panel, and the filament a
print uses is booked to the *active* spool. That much works without this
plugin, with one active spool chosen by hand.

## 2. Install the plugin

Over SSH on the printer:

    cd /data/ad5x/plugins
    su klipper -s /bin/sh -c 'git clone https://github.com/djvalic/kiln-spoolman.git spoolman'

Then in the console (Fluidd or HelixScreen):

    ENABLE_PLUGIN NAME=spoolman

and reboot once, so Moonraker picks up the plugin's update entry. Fluidd
then lists **spoolman** under Settings > Software Updates; after an update,
run `RESTART`.

Removing it: `DISABLE_PLUGIN NAME=spoolman`, then delete
`/data/ad5x/plugins/spoolman`.

## 3. Tell it which spool is in which slot

    SPOOLMAN_SET_SLOT SLOT=1 SPOOL=12
    SPOOLMAN_SET_SLOT SLOT=2 SPOOL=7
    SPOOLMAN_SET_SLOT SLOT=2 SPOOL=        (clears it)
    SPOOLMAN_SLOTS                          (lists them)

From then on every load or swap (T0-T3, `IFS_LOAD`, auto-refill) makes the
loaded slot's spool the active one; emptying the nozzle clears the active
spool. While no slot has a spool the active spool is left alone, so the
plugin does nothing until you set one. The IDs are kept in `variables.cfg`
(`spoolman_slots`); `printer.spoolman_slots.slots` shows them.

If Moonraker has no `[spoolman]` section, setting the active spool fails
quietly (logged in `klippy.log`); prints are never stopped by it.

## Files

| File | What |
|---|---|
| `plugin.json` | Name, version, required plugin API (Kiln OS `docs/plugin-api.md`) |
| `plugin.cfg` | Klipper config: `[spoolman_slots]` |
| `extras/spoolman_slots.py` | The Klipper module |
| `moonraker.conf` | Moonraker's update entry for this repository |
| `test_spoolman_slots.py` | Offline test: `python3 test_spoolman_slots.py` |

## Licence

GPL-3.0, like Klipper.
