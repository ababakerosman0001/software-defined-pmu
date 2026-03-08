
function pmu = run_pmu_estimator(signal, fs, f0)

N  = round(fs/f0);
dt = 1/fs;
total = length(signal);
t_pmu = (0: total-N-1)/fs;



magnitude = zeros(total-N,1);
phase_out = zeros(total-N,1);

win = hanning(N);
correction = N / sum(win);

for a = 1 : (total - N)
    b = a+ N-1;
    window_data = signal(a:b);
   
    window_data = window_data .* win;
    y = fft(window_data);
    
    yk = y(2);
    magnitude(a) = abs(yk) * 2/N * correction / sqrt(2);
    raw_phase = angle(yk)*180/pi;
    phase_correction = mod(360 * 50 * t_pmu(a), 360);
    phase_out(a) = raw_phase - phase_correction;
   
end
phase_out = mod(phase_out + 180, 360) - 180;
phase_out = phase_out + 90;
phase_out = mod(phase_out + 180, 360) - 180;  % rewrap to ±180°


frequency = zeros(size(phase_out));
for n = 2 : length(phase_out)
    delta_phi = phase_out(n)-phase_out(n-1);

    delta_phi = mod(delta_phi+180,360)-180;
    frequency(n) = 50 + delta_phi/(360*dt);
end
frequency(1) = f0 ;
rocof = zeros(size(frequency));
for n = 2 : length(frequency)
    rocof(n) = (frequency(n)-frequency(n-1))/dt ;
   
end 
rocof(1) = 0;
rocof = movmean(rocof,N);
pmu.t_pmu     = t_pmu(:);
pmu.magnitude = magnitude(:);
pmu.phase     = phase_out(:);
pmu.frequency = frequency(:);
pmu.rocof     = rocof(:);

end