"""Spike: Can a Quartz event tap intercept the backtick and swallow it?

Run on macOS: python spike-quartz-tap.py
Open TextEdit, press backtick — if it doesn't appear, the tap works.
Ctrl+C to exit.

One question: does CGEventTapCreate + kCGSessionEventTap + returning NULL
actually prevent the backtick from reaching the focused app?
"""

import sys
import time
import Quartz

TARGET_KEYCODE = 50  # backtick / grave accent on US keyboard

def tap_callback(proxy, event_type, event, refcon):
    if event_type == Quartz.kCGEventKeyDown:
        keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        if keycode == TARGET_KEYCODE:
            print(f"Swallowed backtick (keycode={keycode})")
            return None  # NULL = swallow the event
    elif event_type == Quartz.kCGEventKeyUp:
        keycode = Quartz.CGEventGetIntegerValueField(event, Quartz.kCGKeyboardEventKeycode)
        if keycode == TARGET_KEYCODE:
            return None  # swallow key-up too
    return event  # pass through everything else


def main():
    print("Spike: Quartz event tap — intercept backtick (keycode=50)")
    print("Open TextEdit and press backtick. You should NOT see it appear.")
    print("If it appears, the spike FAILS.")
    print("Press Ctrl+C to exit.\n")

    # Check accessibility permission
    trusted = Quartz.AXIsProcessTrustedWithOptions(
        {Quartz.kAXTrustedCheckOptionPrompt: True}
    )
    if not trusted:
        print("ERROR: Accessibility permission not granted.")
        print("Go to System Preferences → Security & Privacy → Privacy → Accessibility")
        print("Add Terminal (or your terminal app) and retry.")
        return 1

    print(f"Accessibility: GRANTED (trusted={trusted})")

    # Create the event tap
    tap = Quartz.CGEventTapCreate(
        Quartz.kCGSessionEventTap,      # session-level, not HID
        Quartz.kCGHeadInsertEventTap,   # insert at head of queue (before app gets it)
        Quartz.kCGEventTapOptionDefault, # active tap (can swallow events)
        Quartz.CGEventMaskBit(Quartz.kCGEventKeyDown) |
        Quartz.CGEventMaskBit(Quartz.kCGEventKeyUp),
        tap_callback,
        None,
    )

    if tap is None:
        print("ERROR: CGEventTapCreate returned NULL.")
        print("Likely causes: accessibility not granted, or sandbox restriction.")
        return 1

    print(f"Event tap created: {tap}")

    # Add tap to run loop
    run_loop_source = Quartz.CFMachPortCreateRunLoopSource(None, tap, 0)
    Quartz.CFRunLoopAddSource(
        Quartz.CFRunLoopGetCurrent(),
        run_loop_source,
        Quartz.kCFRunLoopCommonModes,
    )

    # Enable the tap
    Quartz.CGEventTapEnable(tap, True)
    print("Tap enabled. Listening...\n")

    # Run the loop
    try:
        Quartz.CFRunLoopRun()
    except KeyboardInterrupt:
        print("\nStopped.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
