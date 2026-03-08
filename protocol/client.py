import socket
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 4712))
print("Connected!")

# receive a few frames
for i in range(5):
    data = client.recv(30)
    print(f"Frame {i+1}: {len(data)} bytes → {data.hex()}")

client.close()