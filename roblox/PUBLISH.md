# Publishing Glass Mall

**Published 28 Oct 2026:** [Glass Mall on Roblox](https://www.roblox.com/games/98868923375548/Glass-Mall) (place 98868923375548, universe 10773321732). It's public for ages 16+. Opening it to under-16s needs Roblox's maturity questionnaire, filled in on the Creator Hub.

**Updated 28 Oct 2026 with Glass City** (place version 3): the open-world city, drivable cars, coins and travel menu.

**Updated 29 Oct 2026** (place version 4): every floor of every building open and furnished, themed mall shops, the explorer passport, the city map, arcade games, free food counters, cinema films, people, sound, weather and fireworks.

The steps below describe the first publish. To update the live game from a rebuilt `GlassMall.rbxlx`, see [Updating the live game](#updating-the-live-game).

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

After you change `build_place.py` or `scripts/*.lua`, run `python3 build_place.py` (it needs numpy) and open the new `GlassMall.rbxlx` in Studio. Then follow [Updating the live game](#updating-the-live-game).

## Updating the live game

Don't use **File › Publish As › Overwrite** from the local file. In Studio 0.745 it freezes on "Upload in progress" and never sends anything. Load the new build into the live place and publish from there instead. `build_place.py` writes `GlassCity_Transfer.rbxmx` for this: one Folder, `__Transfer`, with a folder per service.

1. **File › Open from Roblox › Glass Mall** (or use the window that already has it open).
2. Run this in the command bar to select ServerStorage:
   ```lua
   game:GetService("Selection"):Set({game.ServerStorage})
   ```
3. **File › Import Roblox Model**, pick `roblox/GlassCity_Transfer.rbxmx` (press ⇧⌘G and paste the path), then **Open**. `__Transfer` appears in ServerStorage after a few seconds.
4. Run this in the command bar. It parks the old game in a folder instead of destroying it, so if anything fails, Studio undoes the whole step and nothing is lost:
   ```lua
   local old=Instance.new("Folder") old.Name="__Old" old.Parent=game.ServerStorage for _,s in ipairs({"Workspace","Lighting","ServerScriptService","ReplicatedStorage","ReplicatedFirst"}) do local f=Instance.new("Folder") f.Name=s f.Parent=old for _,c in ipairs(game:GetService(s):GetChildren()) do if not c:IsA("Terrain") and not c:IsA("Camera") then c.Parent=f end end end local f=Instance.new("Folder") f.Name="SPS" f.Parent=old for _,c in ipairs(game.StarterPlayer.StarterPlayerScripts:GetChildren()) do c.Parent=f end local t=game.ServerStorage.__Transfer for _,g in ipairs(t:GetChildren()) do local dest=g.Name=="StarterPlayerScripts" and game.StarterPlayer.StarterPlayerScripts or game:GetService(g.Name) for _,c in ipairs(g:GetChildren()) do c.Parent=dest end end t.Parent=nil old.Parent=nil game.Lighting.Ambient=Color3.fromRGB(128,124,118) workspace.StreamingEnabled=true print("swapped; parts", #workspace:GetDescendants())
   ```
5. Press **Play** to check it, then **Stop**, then **File › Publish** (⌥P). Output should say *Published new changes in "Glass Mall" to Roblox*.

What the command bar can't do in Studio 0.745: read local files (`InsertService:LoadLocalAsset` and `game:GetObjects` with a file path are refused), read or set `Lighting.Technology`, or set `Workspace.StreamingMinRadius` (the property is gone). A command-bar script that errors part-way is undone, except for anything it destroyed. That's why step 4 never calls Destroy.

Saving coins and passports doesn't work in Studio unless **Game Settings › Security › Enable Studio Access to API Services** is on; the errors in Output about it are harmless. It works in the live game.
