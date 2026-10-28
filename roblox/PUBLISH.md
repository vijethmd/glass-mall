# Publishing Glass Mall

**Published 28 Oct 2026:** [Glass Mall on Roblox](https://www.roblox.com/games/98868923375548/Glass-Mall) (place 98868923375548, universe 10773321732). It's public for ages 16+. Opening it to under-16s needs Roblox's maturity questionnaire, filled in on the Creator Hub.

**Updated 28 Oct 2026 with Glass City** (place version 3): the open-world city, drivable cars, coins and travel menu.

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

Don't use **File › Publish As › Overwrite** from the local file. In Studio 0.745 it freezes on "Upload in progress" and never sends anything; it did this three times on 28 Oct, even after a restart. Copy the new build into the live place and publish from there instead:

1. Open the rebuilt `GlassMall.rbxlx`. Run this in the command bar (View › Command Bar) to gather everything into one folder:
   ```lua
   local t=Instance.new("Folder") t.Name="__Transfer" for _,s in ipairs({"Workspace","Lighting","ServerScriptService","ReplicatedStorage"}) do local f=Instance.new("Folder") f.Name=s f.Parent=t for _,c in ipairs(game:GetService(s):GetChildren()) do if not c:IsA("Terrain") and not c:IsA("Camera") then c.Parent=f end end end local f=Instance.new("Folder") f.Name="StarterPlayerScripts" f.Parent=t for _,c in ipairs(game.StarterPlayer.StarterPlayerScripts:GetChildren()) do c.Parent=f end t.Parent=game.ServerStorage print("gathered", #t:GetDescendants())
   ```
   Click **ServerStorage › __Transfer** in the Explorer and choose **Edit › Copy**.
2. **File › Open from Roblox › Glass Mall.** In that window's command bar, clear out the old game. Studio warns that this uses Destroy; click **Continue**.
   ```lua
   for _,s in ipairs({"Workspace","Lighting","ServerScriptService","ReplicatedStorage"}) do for _,c in ipairs(game:GetService(s):GetChildren()) do if not c:IsA("Terrain") and not c:IsA("Camera") then c:Destroy() end end end for _,c in ipairs(game.StarterPlayer.StarterPlayerScripts:GetChildren()) do c:Destroy() end
   ```
3. Select **ServerStorage**, choose **Edit › Paste Into**, then run:
   ```lua
   local t=game.ServerStorage.__Transfer for _,f in ipairs(t:GetChildren()) do local dest=f.Name=="StarterPlayerScripts" and game.StarterPlayer.StarterPlayerScripts or game:GetService(f.Name) for _,c in ipairs(f:GetChildren()) do c.Parent=dest end end workspace.StreamingEnabled=true t.Parent=nil print("moved; parts", #workspace:GetDescendants())
   ```
4. **File › Publish** (Alt+P). Output should say *Published new changes in "Glass Mall" to Roblox*.
5. Close the local `GlassMall.rbxlx` with **Don't Save**, so the file stays as the build script wrote it.

If any command-bar script stops with an error, Studio undoes its moves but not its deletes. Run each script exactly as given; if one fails, paste again and rerun step 3.
