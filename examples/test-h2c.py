from h2spacex import H2Connection
from time import sleep
from h2spacex import h2_frames

h2_conn = H2Connection(
    hostname='nghttp2.org',
    port_number=80
)

headers = """accept: */*
content-type: application/x-www-form-urlencoded
...
"""

stream_ids_list = h2_conn.generate_stream_ids(number_of_streams=5)

all_headers_frames = []  # all headers frame + data frames which have not the last byte
all_data_frames = []  # all data frames which contain the last byte

for s_id in stream_ids_list:
    header_frames_without_last_byte, last_data_frame_with_last_byte = h2_conn.create_single_packet_http2_get_request_frames(
        method='GET',
        headers_string=headers,
        scheme='http',
        stream_id=s_id,
        authority="nghttp2.org",
        path="/"
    )

    all_headers_frames.append(header_frames_without_last_byte)
    all_data_frames.append(last_data_frame_with_last_byte)

# concatenate all headers bytes
temp_headers_bytes = b''
for h in all_headers_frames:
    temp_headers_bytes += bytes(h)

# concatenate all data frames which have last byte
temp_data_bytes = b''
for d in all_data_frames:
    temp_data_bytes += bytes(d)

h2_conn.setup_connection()
h2_conn.send_ping_frame()  # important line (in improved version of single packet attack)

# send header frames
h2_conn.send_frames(temp_headers_bytes)

# wait some time
sleep(0.1)

# send ping frame to warm up connection
h2_conn.send_ping_frame()

# send remaining data frames
h2_conn.send_frames(temp_data_bytes)

# print response of sent requests
resp = h2_conn.read_response_from_socket(_timeout=10)
frame_parser = h2_frames.FrameParser(h2_connection=h2_conn)
frame_parser.add_frames(resp)

h2_conn.close_connection()

for x in frame_parser.headers_and_data_frames.keys():
    sid = str(x)
    d = frame_parser.headers_and_data_frames[x]
    print(f'Stream ID: {sid}, response nano seconds: {d["nano_seconds"]}')
    print(f'Headers: {str(d["header"])}')
    print(f'Body (DATA): {str(d["data"])}')
