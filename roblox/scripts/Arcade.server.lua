-- Prizes for the arcade games (Arcade.client): a few coins for a good score. The server only
-- pays for a game it saw start, that lasted long enough for the score claimed, at most once
-- every 20 seconds per player.
local Players = game:GetService("Players")
local ReplicatedStorage = game:GetService("ReplicatedStorage")

local remote = ReplicatedStorage:WaitForChild("Arcade")
local RULES = { -- most points a second, best score allowed, points per coin
	catch = { rate = 6, best = 150, per = 4 },
	dash = { rate = 2.5, best = 220, per = 3 },
	memory = { rate = 0.6, best = 40, per = 1 },
}
local MAX_PRIZE, COOLDOWN = 15, 20

local started, paid = {}, {}

remote.OnServerEvent:Connect(function(player, action, kind, score, duration)
	local rule = type(kind) == "string" and RULES[kind]
	if not rule then
		return
	end
	if action == "start" then
		started[player] = { kind = kind, at = os.clock() }
		return
	end
	if action ~= "finish" or type(score) ~= "number" or type(duration) ~= "number" then
		return
	end
	local s = started[player]
	started[player] = nil
	if not s or s.kind ~= kind then
		return
	end
	local elapsed = os.clock() - s.at
	score = math.floor(math.clamp(score, 0, rule.best))
	local coins = 0
	if elapsed + 1 >= math.min(duration, 90) and score <= rule.rate * elapsed + 3
		and (not paid[player] or os.clock() - paid[player] > COOLDOWN) then
		coins = math.min(MAX_PRIZE, math.floor(score / rule.per))
	end
	if coins > 0 then
		paid[player] = os.clock()
		local stats = player:FindFirstChild("leaderstats")
		local value = stats and stats:FindFirstChild("Coins")
		if value then
			value.Value += coins
		end
	end
	remote:FireClient(player, "prize", coins)
end)

Players.PlayerRemoving:Connect(function(player)
	started[player] = nil
	paid[player] = nil
end)
