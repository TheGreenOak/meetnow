const net = require("net");

let sock = new net.Socket();
sock.connect(5060, "127.0.0.1");

sock.on("data", (data) => {
  console.log(data.toString());
});

sock.on("error", (err) => {
  console.error(err);
});

sock.write('{"request": "end"}');

setTimeout(() => { sock.destroy(); }, 500);

setTimeout(() => {
  sock.connect(5060, "127.0.0.1");
  sock.write('{"request": "end"}');

  setTimeout(() => { sock.destroy(); }, 500);
}, 1000);

console.log("Test");
