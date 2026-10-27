# Publishing Glass Mall

**Published 28 Oct 2026:** [Glass Mall on Roblox](https://www.roblox.com/games/98868923375548/Glass-Mall) (place 98868923375548, universe 10773321732). It's public for ages 16+. Opening it to under-16s needs Roblox's maturity questionnaire, filled in on the Creator Hub.

The steps below describe the first publish. To update the live game from a rebuilt `GlassMall.rbxlx`, open the file in Studio, choose **File › Publish As**, pick the **Glass Mall** experience, select its **Glass Mall** place and click **Overwrite**.

`GlassMall.rbxlx` is already open in Roblox Studio and signed in to your account. Publishing takes about five minutes.

## 1. Try it (1 minute)

Press **Play** (F5) in Studio. You start on the entrance court. Walk to the glass doors; they slide open. Ride an escalator, call the lift, and sit in a cinema seat. Then press **Travel › Stunt park**, hold **E** on the glowing pad to get a car, and drive with W/A/S/D. Press **Stop** (Shift+F5) when you're done.

If anything goes wrong, open **View › Output** and copy the red lines.

## 2. Publish (1 minute)

1. **File › Publish to Roblox** (Alt+P).
2. Choose **Create a new experience** and fill it in:
   - **Name:** `Glass Mall`
   - **Description:** paste the text below.
   - **Genre:** Town and City, or Roleplay if that is the closest option offered.
   - **Devices:** Computer, Phone, Tablet.
3. Click **Create**. Studio uploads the place and shows the experience's page link.

> Explore Glass Mall, a five-storey glass shopping mall built from real architecture floor plans, and the whole city around it. Walk in through the sliding doors, ride the escalators or the glass lift, catch a film in the 4F cinemas, then grab a car and drive Glass City: a ring highway, downtown towers, Central Park and its lake, the VAYU hotel and its sky pool, a stunt park with a mega ramp, and a beach with a pier. Collect gold coins everywhere, and watch the city light up at night.

## 3. Make it public (2 minutes)

New experiences are private. To let everyone play it:

1. Open **Home › Game Settings** in Studio.
2. **Basic Info:** set **Max players** to 20 if you're asked.
3. **Permissions › Playability:** choose **Public**, then **Save**.
4. If Roblox asks for the **Maturity & Compliance questionnaire** first, answer **No** to every question. The game has no violence, blood, romance, gambling or paid items, so it rates **Minimal**.

The game page link has the form `https://www.roblox.com/games/<place id>/Glass-Mall`. You can also find it under **Creations** at https://create.roblox.com.

## 4. Tell your friend

A draft email to **marshmellowfan300@gmail.com** is waiting in your Gmail drafts (subject: *Glass Mall is live on Roblox*). Replace `[GAME LINK]` with the link from step 3 and click **Send**.

If you'd rather I send it, tell me the link and I'll finish and send the draft.

## Rebuilding

After you change `build_place.py` or `scripts/*.lua`, run `python3 build_place.py` (it needs numpy) and open the new `GlassMall.rbxlx` in Studio. Republish with **File › Publish As › Glass Mall › Overwrite** to update the live game.
