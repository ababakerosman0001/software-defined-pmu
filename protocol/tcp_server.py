import struct
import math
import socket 
import time
import scipy.io
import datetime

# load phase 3 data
data = scipy.io.loadmat('data.mat')

def crc_ccitt(data):
    crc = 0xFFFF
    for byte in data :
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = (crc<<1) ^ 0x1021
            else :
                crc = (crc<<1)
            crc &= 0xFFFF
    return crc
def build_data_frame(soc, fracsec, magnitude, phase_deg, frequency, rocof, idcode=7,NOMFREQ = 50):
    sync = struct.pack('>H',0xAA01)
    idcode = struct.pack('>H',idcode)
    soc = struct.pack('>I',soc)
    stat = struct.pack('>H',0x0000)
    quality = 0x00
    total_frac = (quality<<24) | fracsec
    total_frac = struct.pack('>I',total_frac)
    real = magnitude * math.cos(math.radians( phase_deg))
    imag = magnitude * math.sin(math.radians( phase_deg))
    phasor = struct.pack('>ff',real , imag)   

    freq_val =  round((frequency - NOMFREQ)*1000)
    freq_val = max(-32768, min(32767, freq_val))
    freq_bytes = struct.pack('>h',freq_val )

    dfreq_val = round(rocof * 100)
    dfreq_val = max(-32768, min(32767, dfreq_val))
    dfreq_bytes = struct.pack('>h',dfreq_val)
    framesize = struct.pack('>H',30)
    frame = sync + framesize + idcode + soc + total_frac + stat + phasor + freq_bytes + dfreq_bytes
    chk = struct.pack('>H',crc_ccitt(frame))
    c37_frame = frame + chk
    return c37_frame
def build_config_frame(soc, fracsec, idcode=7, data_rate=50):

    
    # SYNC for config frame 2
    sync = struct.pack('>H', 0xAA31)
    
    # IDCODE
    idcode_bytes = struct.pack('>H', idcode)
    
    # SOC and FRACSEC
    soc_bytes    = struct.pack('>I', soc)
    quality      = 0x00
    fracsec_full = (quality << 24) | fracsec
    fracsec_bytes = struct.pack('>I', fracsec_full)
    
    # TIME_BASE
    time_base = struct.pack('>I', 1000000)
    
    # NUM_PMU
    num_pmu = struct.pack('>H', 1)
    
    # STN - station name (16 bytes)
    stn = 'PMU_BUS2'.encode('ascii').ljust(16)   # fill in correct name
    
    # FORMAT
    fmt = struct.pack('>H', 0x0002)              # fill in correct value
    
    # PHNMR, ANNMR, DGNMR
    phnmr = struct.pack('>H', 1)
    annmr = struct.pack('>H', 0)
    dgnmr = struct.pack('>H', 0)
    
    # CHNAM - channel name (16 bytes)
    chnam = 'VA'.encode('ascii').ljust(16)        # fill in correct name
    
    # PHUNIT
    phunit = struct.pack('>I', 0x00000000)
    
    # FNOM - nominal frequency
    # 0x0001 = 50Hz, 0x0000 = 60Hz
    fnom = struct.pack('>H', 0x0001)
    
    # CFGCNT
    cfgcnt = struct.pack('>H', 0)
    
    # DATA_RATE
    data_rate_bytes = struct.pack('>H', data_rate)
    
    # assemble without FRAMESIZE and CHK
    body = (idcode_bytes + soc_bytes + fracsec_bytes +
            time_base + num_pmu + stn + idcode_bytes +
            fmt + phnmr + annmr + dgnmr + chnam +
            phunit + fnom + cfgcnt + data_rate_bytes)
    
    # compute framesize
    # SYNC(2) + FRAMESIZE(2) + body + CHK(2)
    framesize = 2 + 2 + len(body) + 2
    framesize_bytes = struct.pack('>H', framesize)
    
    # assemble full frame without CHK
    frame = sync + framesize_bytes + body
    
    # compute and append CRC
    chk = struct.pack('>H', crc_ccitt(frame))
    frame = frame + chk
    
    return frame
def send_frames(frames , port = 4712 , frame_rate = 50):
    server = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
    server.bind(("0.0.0.0",4712))
    server.listen(1)
    print("PMU server listening on port 4712...")


    while True :
        conn , addr = server.accept()
        print(f"PDC connected from {addr }")
        conn.setsockopt(socket.IPPROTO_TCP , socket.TCP_NODELAY,1)
        try:
            cfg = build_config_frame(soc=826144644, fracsec=0)
            conn.sendall(cfg)
            print("Config frame sent")

            # Step 2: small delay
            time.sleep(0.1)

        
            duration = 1/frame_rate
            next_deadline = time.time()
            while True :
                for frame in frames :
                    conn.sendall(frame)
                    next_deadline += duration
                    sleep_time = next_deadline - time.time()
                    if sleep_time > 0 :
                        time.sleep(sleep_time)

                print( "All frames sent")

        except(BrokenPipeError, ConnectionResetError, OSError):
            print("PDC disconnected")
        finally:
            conn.close()
def get_current_soc_fracsec():
    t_now   = datetime.datetime.now(datetime.timezone.utc)
    t_epoch = datetime.datetime(2000, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
    
    diff         = (t_now - t_epoch).total_seconds()
    soc          = int(diff)
    fracsec      = int((diff - soc) * 1_000_000)
    
    return soc, fracsec



SOC_vec       = data['pmu_output']['SOC'][0][0].flatten()
FRACSEC_vec   = data['pmu_output']['FRACSEC'][0][0].flatten()
magnitude_vec = data['pmu_output']['magnitude'][0][0].flatten()
phase_vec     = data['pmu_output']['phase'][0][0].flatten()
frequency_vec = data['pmu_output']['frequency'][0][0].flatten()
rocof_vec     = data['pmu_output']['rocof'][0][0].flatten()
frames = []
crc_errors = 0
for i in range(len(SOC_vec)):
    frame = build_data_frame(
        soc       = int(SOC_vec[i]),
        fracsec   = int(FRACSEC_vec[i]),
        magnitude = float(magnitude_vec[i]),
        phase_deg = float(phase_vec[i]),
        frequency = float(frequency_vec[i]),
        rocof     = float(rocof_vec[i]),
        idcode    = 7
    )
    frames.append(frame)

    # print(f"Total frames built: {len(frames)}")
    # print(f"Total bytes:        {sum(len(f) for f in frames)}")
    # print(f"\nFirst frame:  {frames[0].hex()}")
    # print(f"Fault frame:  {frames[1000].hex()}")
    # print(f"Last frame:   {frames[-1].hex()}")
for f in frames:
    if crc_ccitt(f[:-2]) != struct.unpack('>H', f[-2:])[0]:
        crc_errors += 1
with open('frames.bin', 'wb') as f:
    for frame in frames:
        f.write(frame)


soc, fracsec = get_current_soc_fracsec()
cfg = build_config_frame(soc=soc, fracsec=fracsec)
send_frames(frames, port=4712, frame_rate=50)


























# print(f"\nCRC errors: {crc_errors} (expected 0)")
# print(f"Real: {real:.4f}")   # expected: 61.2276
# print(f"Imag: {imag:.4f}")   # expected: 35.3500

# print(f"PHASOR: {phasor.hex()}")

# print(f"Phasor bytes: {len(phasor)}")  # expected: 8


# print(f"FREQ: {freq_bytes.hex()}")
# print(f"DFREQ: {dfreq_bytes.hex()}")





