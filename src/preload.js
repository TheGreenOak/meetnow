const net = require('net');
const { contextBridge, ipcRenderer } = require('electron');

let sock = new net.Socket();

contextBridge.exposeInMainWorld("nodejs", {
    myTest: test
});

console.log(sock);
console.log(typeof(sock));

function test() {
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
}