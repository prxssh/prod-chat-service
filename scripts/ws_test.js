import ws from 'k6/ws';
import { check, sleep } from 'k6';

export let options = {
  stages: [
    { duration: '1m', target: 1500 },
    { duration: '1m', target: 3000 },
    { duration: '1m', target: 4500 },
    { duration: '1m', target: 5500 },
    { duration: '1m', target: 3000 },
    { duration: '1m', target: 1500 },
    { duration: '1m', target: 0 },
  ],
};

export default function () {
  const url = 'ws://nginx:80/ws/chat/';
  let seenFirst = false;

  const res = ws.connect(url, null, (socket) => {
    socket.on('open', () => {
        socket.send('ping')
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
      } else {
        check(data, {
          'count incremented to one': (d) => d.count === 1,
        });
        //socket.close();
      }
    });

    socket.setInterval(() => socket.send('ping'), 10000)
    socket.setTimeout(() => socket.close(), 30000);
  });

  check(res, {
    'connected (101)': (r) => r && r.status === 101,
  });

  sleep(5);
}
