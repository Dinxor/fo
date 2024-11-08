import os
import io
from random import randint

import asyncio
import uvicorn
import aiofiles
from fastapi import FastAPI, Request, File, UploadFile, Query, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, StreamingResponse
import qrcode

from db import DataBase
db = DataBase()

app = FastAPI(docs_url=None, redoc_url=None)

u_page  ='''<!DOCTYPE html>
<html xml:lang="ru-ru" lang="ru-ru">
<head>
    <title>Управление файлами</title>
</head>
<body>
    <a href="qr" 
        target="popup" 
        onclick="window.open('./qr','popup','width=600,height=600'); return false;">
        Показать QR
    </a>
    <h2>Загрузка файла</h2>
    <form action="/fo" method="post" enctype="multipart/form-data">
        <!-- File input field -->
        <input type="file" id="file" name="file" multipart>
        <br><br>
        <!-- Submit button -->
        <input type="submit" value="Загрузить">
    </form>
    <h2>Скачивание файла</h2>
    <form action="/fo" method="get">
        <!-- Code input field -->
        <label for="code">Введите код файла :</label>
        <input type="text" id="file" name="file">
        <br><br>
        <!-- Submit button -->
        <input type="submit" value="Скачать">
    </form>
</body>
</html>'''


done_page  ='''<!DOCTYPE html>
<html>
<head>
    <title>Файл загружен</title>
</head>
<body>
    <a href="../fo">На главную</a>
    <a href="qr" 
        target="popup" 
        onclick="window.open('./qr','popup','width=600,height=600'); return false;">
        Показать QR
    </a><br>
    <h2>Загрузка файла завершена</h2>
    Код для скачивания файла {fileid}, также файл доступен по ссылке<br>
    <a href="../fo?file={fileid}"> Скачать файл {filename}</a>
    <a href="qr" 
        target="popup" 
        onclick="window.open('./qr?file={fileid}','popup','width=600,height=600'); return false;">
        Показать QR
    </a><br>
</body>
</html>'''


nof_page  ='''<!DOCTYPE html>
<html>
<head>
    <title>Файл не найден</title>
</head>
<body>
    <a href="../fo">На главную</a>
    <a href="qr" 
        target="popup" 
        onclick="window.open('./qr','popup','width=600,height=600'); return false;">
        Показать QR
    </a>
    <br>
    <h2>Такого файла нет на сервере</h2>
</body>
</html>'''


async def init_data():
    await db.create_table_files()
    data = await db.get_all_files()
    for (filename, fileid) in data:
        files.update({int(fileid): filename})


@app.get("/")
@app.get('/fo', response_class=HTMLResponse)
async def fo_page(file: str = Query(default="")):
    if file:
        fileid = int(file)
        filename = files.get(fileid, '')
        if filename:
            return FileResponse(path=f'files/{fileid}/{filename}', filename=filename)
        else:
            return HTMLResponse(nof_page)
    else:
        return HTMLResponse(u_page)


@app.post("/fo")
async def upload(file: UploadFile = File(...)):
    if file.filename:
        fileid = randint(10000, 99999)
        while fileid in files.keys():
            fileid = randint(10000, 99999)
        save_dir = f'files\\{fileid}'
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        try:
            async with aiofiles.open(f'{save_dir}\\{file.filename}', 'wb') as f:
                while contents := file.file.read(1024 * 1024):
                    await f.write(contents)
        except Exception:
            return {"message": "There was an error uploading the file"}
        finally:
            file.file.close()
            files.update({fileid: file.filename})
            await db.add_file_to_table(file.filename, fileid)
        return HTMLResponse(done_page.format(fileid = fileid, filename = file.filename))
    else:
        return HTMLResponse(u_page)


@app.get('/qr')
async def link_qr(request: Request):
    try:
        host = request.headers.get('host')
        code = request.query_params.get('file', '')
        if code:
            url = f'http://{host}/fo?file={code}'
        else:
            url = f'http://{host}/fo'
        print(host, code, url)
        img = qrcode.make(url)
        buf = io.BytesIO()
        img.save(buf, format='png')
        buf.seek(0)
        return StreamingResponse(content=buf, media_type="image/png",
                headers={'Content-Disposition': 'inline'})
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    files = {}
    asyncio.run(init_data())
    uvicorn.run(app, host = '0.0.0.0', port = 8000)