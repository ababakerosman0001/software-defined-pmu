%t_now = datetime('now','TimeZone','UTC')
%t_epoch = datetime(2000,1,1,0,0,0,'TimeZone','UTC')
%dt = t_now-t_epoch
%p_epoch = posixtime(t_epoch)
%p_epoch = posixtime(datetime(2000,1,1,0,0,0,'TimeZone','UTC'))
%dp  = p_now-p_epoch
%SOC = floor(dp) 
function [SOC, FRACSEC] = to_timestamp(t_sim, t_epoch)

  TIME_BASE = 1000000 ;
  t_absolute = t_epoch + t_sim;
  SOC        = floor(t_absolute);
  frac       = t_absolute - SOC;
  FRACSEC    = round(frac * TIME_BASE);
  rollover = FRACSEC >= TIME_BASE;
SOC      = SOC + rollover;
FRACSEC  = FRACSEC - rollover * TIME_BASE;
end