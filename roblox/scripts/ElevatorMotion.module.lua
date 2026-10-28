-- How a lift car moves between two heights: it eases up to its cruising speed along a
-- cosine curve, cruises, and eases down again, so there is no jolt at either end.
-- The server uses it to know when the car arrives; every player's screen uses it to draw
-- the car at the same height at the same moment (both run on workspace:GetServerTimeNow()).
local Motion = {}

Motion.ACCEL = 24 -- studs/s^2, the average while speeding up or slowing down

function Motion.plan(from, to, vmax)
	local distance = math.abs(to - from)
	local cruise = math.min(vmax, math.sqrt(distance * Motion.ACCEL / 2))
	if cruise < 1e-3 then
		return { from = from, to = to, cruise = 0, ramp = 0, flat = 0, duration = 0 }
	end
	local ramp = 2 * cruise / Motion.ACCEL
	local flat = math.max(0, (distance - cruise * ramp) / cruise)
	return { from = from, to = to, cruise = cruise, ramp = ramp, flat = flat, duration = 2 * ramp + flat }
end

-- distance covered t seconds after leaving, and the speed at that moment
function Motion.travelled(plan, t)
	local v, ta, flat = plan.cruise, plan.ramp, plan.flat
	local distance = math.abs(plan.to - plan.from)
	if t <= 0 or plan.duration <= 0 then
		return 0, 0
	elseif t >= plan.duration then
		return distance, 0
	end
	local function eased(s)
		return v / 2 * (s - ta / math.pi * math.sin(math.pi * s / ta)), v / 2 * (1 - math.cos(math.pi * s / ta))
	end
	if t < ta then
		return eased(t)
	elseif t < ta + flat then
		return v * ta / 2 + v * (t - ta), v
	end
	local d, speed = eased(plan.duration - t)
	return distance - d, speed
end

function Motion.height(plan, t)
	local d, speed = Motion.travelled(plan, t)
	local sign = plan.to >= plan.from and 1 or -1
	return plan.from + sign * d, sign * speed
end

return Motion
