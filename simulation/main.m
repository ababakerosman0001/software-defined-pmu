pmu1 = run_pmu_estimator(Vbus2(:,1), 10000, 50);
%% Visualisation

figure(1)
subplot(4,1,1)
plot(pmu1.t_pmu, pmu1.magnitude)
title('Magnitude (V RMS)'); grid on
xline(0.1,'r--'); xline(0.2,'g--')

subplot(4,1,2)
plot(pmu1.t_pmu, pmu1.phase)
title('Phase (degrees)'); grid on
xline(0.1,'r--'); xline(0.2,'g--')

subplot(4,1,3)
plot(pmu1.t_pmu, pmu1.frequency)
title('Frequency (Hz)'); grid on
xline(0.1,'r--'); xline(0.2,'g--')

subplot(4,1,4)
plot(pmu1.t_pmu, pmu1.rocof)
title('ROCOF (Hz/s)'); grid on
xline(0.1,'r--'); xline(0.2,'g--')

% save for Phase 3
save('data.mat', 'pmu1')

%% Attaching Timestamps

% compute epoch
t_now   = datetime('now', 'TimeZone', 'UTC');
t_epoch = datetime(2000, 1, 1, 0, 0, 0, 'TimeZone', 'UTC');
epoch_SOC = floor(posixtime(t_now) - posixtime(t_epoch));
[SOC_vec, FRACSEC_vec] = to_timestamp(pmu1.t_pmu, epoch_SOC);



pmu_output.IDCODE    = 1;
pmu_output.TIME_BASE = 1000000;
pmu_output.SOC       = SOC_vec;
pmu_output.FRACSEC   = FRACSEC_vec;
pmu_output.magnitude = pmu1.magnitude;
pmu_output.phase     = pmu1.phase;
pmu_output.frequency = pmu1.frequency;
pmu_output.rocof     = pmu1.rocof;

fprintf('=== Timestamp Validation ===\n')
fprintf('Total phasors:     %d\n',   length(SOC_vec))
fprintf('Unique SOC values: %d\n',   length(unique(SOC_vec)))
fprintf('Min FRACSEC:       %d\n',   min(FRACSEC_vec))
fprintf('Max FRACSEC:       %d\n',   max(FRACSEC_vec))



save('data.mat', 'pmu_output')


fprintf('Phase Error Analysis\n')
timing_errors = [1e-6, 10e-6, 31e-6, 100e-6, 1e-3];
labels = {'1us', '10us', '31us', '100us', '1ms'};

for i = 1:length(timing_errors)
    phase_error = 360 * 50 * timing_errors(i);
    fprintf('Timing error %s → phase error = %.4f degrees\n', labels{i}, phase_error)
end

fprintf('\nCompliance boundary (0.573 degrees) at: %.1f us\n', 0.573/(360*50)*1e6)

