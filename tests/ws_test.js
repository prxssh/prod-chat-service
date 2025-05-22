import ws from 'k6/ws';
import { check, sleep } from 'k6';

export let options = {
  vus: 50,         // 50 concurrent virtual users
  duration: '30s', // total test duration
};

export default function () {
  const url = 'ws://localhost/ws/chat/?session=k6_test';
  let seenFirst = false;

  const res = ws.connect(url, null, (socket) => {
    socket.on('open', () => {
      // handshake complete
    });

    socket.on('message', (raw) => {
      let data;
      try {
        data = JSON.parse(raw);
      } catch {
        return;
      }

      if (!seenFirst) {
        check(data, {
          'initial session_id is string': (d) => typeof d.session_id === 'string',
          'initial count is zero':       (d) => d.count === 0,
        });
        seenFirst = true;
        socket.send('ping'); // trigger the next message
      } else {
        // response to our ping
        check(data, {
          'count incremented to one': (d) => d.count === 1,
        });
        socket.close();
      }
    });

    socket.setTimeout(() => socket.close(), 10000);
  });

  check(res, {
    'connected (101)': (r) => r && r.status === 101,
  });

  sleep(1);
}
