-- Moves a player to a place picked in the Travel menu.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local PLACES = __PLACES__ -- name -> position in studs
local event = ReplicatedStorage:WaitForChild("Travel")
local last = {}

event.OnServerEvent:Connect(function(player, name)
	local pos = type(name) == "string" and PLACES[name]
	local character = player.Character
	local humanoid = character and character:FindFirstChildOfClass("Humanoid")
	if not pos or not humanoid or humanoid.Health <= 0 then
		return
	end
	if last[player] and os.clock() - last[player] < 2 then
		return
	end
	last[player] = os.clock()
	humanoid.Sit = false
	task.wait(0.15)
	pcall(function()
		player:RequestStreamAroundAsync(pos)
	end)
	character:PivotTo(CFrame.new(pos + Vector3.new(0, 4, 0)))
end)

Players.PlayerRemoving:Connect(function(player)
	last[player] = nil
end)
