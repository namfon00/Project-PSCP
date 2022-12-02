from fastapi import FastAPI, Request, Form, Cookie
from fastapi.responses import HTMLResponse, Response
from pyngrok import ngrok as ngrokModule
import json
import os

app = None
config = None
cur_path_of_py_file = None
adminTemPath = None
admin_redirect = None
ngrok = None
ngrokLink = ""
parent_path = None
radminToken = ""
render_templates = None
redirect = None
alert = None
alert_mss = ""
serverOS = ""

def adminSys():
    """admin system ระบบแอดมิน"""
    global app
    def setNgrok():
        """Create Ngrok tunnle Or Kill tunnle สร้างและค่าTunnle"""
        global ngrokLink
        if bool(config["ngrok"]["on"]) and config["ngrok"]["token"] != "" and ngrokLink == "":
            ngrokModule.set_auth_token(config["ngrok"]["token"])
            ngrokLink = "<tr><th>%s</th></tr>" % ngrokModule.connect(
                config["port"])
            print(ngrokLink)
        elif not bool(config["ngrok"]["on"]):
            ngrokLink = ""
            ngrokModule.kill()
    setNgrok()

    def render_adminTemplates(content:str = ""):
        global alert_mss
        _alert = f"<script>{alert(mss = alert_mss)}</script>" if alert_mss != "" else ""
        result_html = render_templates(path = adminTemPath, data = {"content":content,"alert":_alert})
        alert_mss = ""
        return result_html

    @app.get("/admin")
    def admin(adminToken: str = Cookie(None)):
        """
        หน้าแรกส่วนการตั้งค่า
        + Input
            + adminToken
        + Output
            + หน้า Login
            + หน้า welcome
            + Cookie (For Token)
        """
        index_html = open(cur_path_of_py_file +"/admin_templates/admin-login.txt", "r", encoding="utf-8").read()
        if adminToken == radminToken:
            welcome_html = open(cur_path_of_py_file +"/admin_templates/admin-welcome.txt", "r", encoding="utf-8").read()
            welcome_html = render_templates(
                path = cur_path_of_py_file +"/admin_templates/admin-welcome.txt",
                data = {"ngrokLinkBox": render_templates(
                    path = cur_path_of_py_file+"/admin_templates/admin-welcome-showNgrokLink.txt", 
                    data = {"ngrokLink": ngrokLink}) if ngrokLink != "" else ""})
            return HTMLResponse(render_adminTemplates(content = welcome_html))
        return HTMLResponse(render_adminTemplates(content = index_html))


    @app.post("/admin")
    def admin_login(adminToken: str = Form("")):
        """
        ตรวจความถูกต้องของโทเค็น
        + Input
            + adminToken
        + Output
            + Cookie (เมื่อTokenผิด)
        """
        global alert_mss
        if adminToken == radminToken:
            response = HTMLResponse(admin_redirect)
            response.set_cookie(key="adminToken", value=adminToken)
            alert_mss = "Login Success ล็อกอินสำเร็จ"
            return response
        response = HTMLResponse(redirect("/admin"))
        response.delete_cookie(key="adminToken")
        alert_mss = "Wrong Token โทเค็นผิดพลาด"
        return response


    @app.get("/admin/logout")
    def logout(adminToken = Cookie("")):
        """
        ออกจากระบบ
        + ทำการลบ Cookie
        """
        global alert_mss
        if adminToken == radminToken:
            alert_mss = "Goodbye ;)"
        response = HTMLResponse(admin_redirect)
        response.delete_cookie(key="adminToken")
        return response


    @app.get("/admin/config")
    def config_html(adminToken=Cookie("")):
        """
        หน้าการกำหนดค่า
        + Input
            + adminToken
        """
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        data_config = {
            "port": config["port"],
            "path": config["parent path"],
            "home": config["template"]["home"],
            "addSound": config["template"]["add_sound"],
            "info": config["template"]["info"],
            "err404": config["template"]["err404"],
            "soundData": config["local_storage"]["sound data"],
            "soundStorage": config["local_storage"]["sound path"],
            "withGsheetCheck": "checked" if config["with_gform_and_gsheet"]["on"] else "",
            "gFormLink": config["with_gform_and_gsheet"]["form_link"],
            "sheetLink": config["with_gform_and_gsheet"]["sheet_link"],
            "sheetLinkCSV": config["with_gform_and_gsheet"]["csv_link"],
            "ngrokLink": ngrokLink,
            "ngrokCheck": "checked" if config["ngrok"]["on"] else "",
            "ngrokToken": config["ngrok"]["token"],
            "serverOS": serverOS
        }
        return HTMLResponse(render_adminTemplates(
            content = render_templates(
                path = cur_path_of_py_file+"/admin_templates/admin-config.txt", 
                data = data_config
                )
            ))


    @app.post("/admin/config")
    def set_config(
            adminToken=Cookie(""),
            port: str = Form(config["port"]),
            path: str = Form(""),
            home: str = Form(""),
            addSound: str = Form(""),
            info: str = Form(""),
            err404:str = Form(""),
            storageType: str = Form(""),
            sheetLink: str = Form(""),
            sheetLinkCSV: str = Form(""),
            gFormLink: str = Form(""),
            ngrok: bool = Form(""), ngrokToken: str = Form("")):
        """
        บันทึกค่าการตั้งค่าลงไฟล์ เจสัน
        + Input
            + adminToken
            + port (fix)
            + path
            + (path .... page)
                + home 
            + storageType
                + sheetLink
                + sheetLinkCSV
                + gFormLink
            + ngrok
                + ngrokToken
        """
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        global config, ngrokLink, alert_mss
        # config หลัก
        config_js = open(cur_path_of_py_file+"/data/config.json", "w", encoding="utf-8")
        config["port"] = port
        config["parent path"] = path
        config["template"]["home"] = home
        config["template"]["add_sound"] = addSound
        config["template"]["info"] = info
        config["template"]["err404"] = err404
        # config ประเภทที่เก็บข้อมูล และ ที่อยู่ของข้อมูล
        if storageType == "local":
            config["with_gform_and_gsheet"]["on"] = 0
            config["local_storage"]["on"] = 1
        else:
            config["with_gform_and_gsheet"]["on"] = 1
            config["local_storage"]["on"] = 0
        config["with_gform_and_gsheet"]["form_link"] = gFormLink
        config["with_gform_and_gsheet"]["sheet_link"] = sheetLink
        config["with_gform_and_gsheet"]["csv_link"] = sheetLinkCSV
        # config ngrok
        if ngrok:
            config["ngrok"]["on"] = 1
            config["ngrok"]["token"] = ngrokToken
            setNgrok()
        else:
            config["ngrok"]["on"] = 0
            config["ngrok"]["token"] = ngrokToken
            setNgrok()
        config_js.write(json.dumps(config))
        config_js.close()
        alert_mss = "saved successfully บันทึกสำเร็จ"
        return HTMLResponse(redirect("/admin/config"))


    @app.get("/admin/edit")
    def showFileCanEdit(adminToken=Cookie("")):
        """
        หน้าแก้ไขไฟล์
        + Input
            + adminToken
            + ?filepath
        + Output
            + รายการไฟล์ต่างๆ
        """
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        ct = ""
        for file_name in os.listdir(parent_path+"/templates"):
            ct += f"""<tr><td>
            <a class="list-admin-content" href='./edit/template?filepath={"/templates/"+file_name}'>
                <span class="material-symbols-outlined">draft</span>
                {file_name}
            </a>
            </td></tr>\n"""
        ct = render_templates(open(cur_path_of_py_file+"/admin_templates/admin-edit.txt", "r", encoding="utf-8").read(),
                            {"templateFiles": ct})
        if config["with_gform_and_gsheet"]["on"]:
            ct = render_templates(ct, {"soundData": f"""
                <p>View Only (Edit at <a href="{config["with_gform_and_gsheet"]["sheet_link"]}">Link)</a></p>
                <iframe width="100%" height="100%" style="min-height: 500px;" src="{config["with_gform_and_gsheet"]["csv_link"][:config["with_gform_and_gsheet"]["csv_link"].find("&")]}" ></iframe>
            """})
        else:
            data_sound = json.loads(open(parent_path+config["local_storage"]["sound data"], "r", encoding="utf-8").read())
            data_sound_table = ""
            for sound_id in data_sound:
                data_sound_table += render_templates(
                    path=cur_path_of_py_file+"/admin_templates/admin-edit-dataSoundRow.txt",
                    data={
                    "id":sound_id,
                    "name":data_sound[sound_id]["name"],
                    "des":data_sound[sound_id]["description"],
                    "soundFile": f'/stream/sound/{sound_id}',
                    "editLink": f"/admin/edit/sound_data/{sound_id}"
                    })
            data_sound_table = render_templates(
                path=cur_path_of_py_file+"/admin_templates/admin-edit-dataSound.txt",
                data={"soundDataRows": data_sound_table})
            ct = render_templates(ct, {"soundData": data_sound_table})
        index_html = render_adminTemplates(content = ct)
        return HTMLResponse(index_html)

    @app.get("/admin/edit/template")
    def edit_templates(adminToken=Cookie(""), filepath: str = ""):
        """Inprogress"""
        global alert_mss
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        if filepath != "":
            return HTMLResponse(render_adminTemplates(
                content = render_templates(
                    path = cur_path_of_py_file+"/admin_templates/admin-edit-textarea.txt", 
                    data = { "filePath":filepath,
                            "textFile":render_templates(path=parent_path+"/"+filepath)
                    })
            ))
        alert_mss = "Error : Invaild arguments"
        return redirect("/admin/edit")

    @app.post("/admin/edit/template")
    def save_file_from_admin_edit(adminToken=Cookie(""), textFile:str=Form(""), pathFile=Form("")):
        """
        บันทึกไฟล์ จากหน้าEdit
        + Input
            + textFile
            + pathFile
        + Output
            + ไฟล์ / ข้อมูล ท่ีบันทึกแล้ว
        """
        global alert_mss
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        file_ = open(parent_path+"/"+pathFile, "w", encoding="utf-8")
        file_.write(textFile)
        file_.close()
        alert_mss = "saved successfully บันทึกสำเร็จ"
        return HTMLResponse(redirect("/admin/edit"))

    @app.get("/admin/edit/sound_data/{id}")
    def edit_soundData(adminToken=Cookie(""),id:str = ""):
        global alert_mss
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        elif config["local_storage"]["on"] == 0:
            alert_mss = "กรุณาใช้การแก้ไขใน Google Sheet แทน"
            return HTMLResponse(redirect("/admin/edit"))
        soundData = json.loads(open(parent_path+config["local_storage"]["sound data"],"r",encoding="utf-8").read())
        return HTMLResponse(
                render_adminTemplates(
                    content = render_templates(
                        path = cur_path_of_py_file+"/admin_templates/admin-edit-editSoundData.txt",
                        data = {
                            "id":id,
                            "soundName":soundData[id]["name"],
                            "description":soundData[id]["description"]
                        }
                        )
                    )
                )

    @app.post("/admin/edit/sound_data/{id}")
    def save_soundData(adminToken=Cookie(""),id:str= "",
    soundName:str = Form(""),
    soundDescription:str = Form("")):
        global alert_mss
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        elif config["local_storage"]["on"] == 0:
            alert_mss = "กรุณาใช้การแก้ไขใน Google Sheet แทน"
            return HTMLResponse(redirect("/admin/edit"))
        soundData = json.loads(open(parent_path+config["local_storage"]["sound data"],"r",encoding="utf-8").read())
        soundData[id]["name"] = soundName if soundName != "" else soundData[id]["name"]
        soundData[id]["description"] = soundDescription if soundDescription != "" else soundData[id]["description"]
        soundDataJson = open(parent_path+config["local_storage"]["sound data"],"w",encoding="utf-8")
        soundDataJson.write(json.dumps(soundData))
        soundDataJson.close()
        alert_mss = "saved successfully บันทึกสำเร็จ"
        return HTMLResponse(redirect("/admin/edit"))
    
    @app.get("/admin/edit/sound_data/delete/{id}")
    def delete_soundData(adminToken=Cookie(""),id:str=""):
        global alert_mss
        if adminToken != radminToken:
            return HTMLResponse(admin_redirect)
        elif config["local_storage"]["on"] == 0:
            alert_mss = "กรุณาใช้การแก้ไขใน Google Sheet แทน"
            return HTMLResponse(redirect("/admin/edit"))
        file_list = os.listdir(parent_path+config["local_storage"]["sound path"])
        soundData = json.loads(open(parent_path+config["local_storage"]["sound data"],"r",encoding="utf-8").read())
        if id+".mp3" in file_list and id in soundData:
            soundData.pop(id)
            soundDataJson = open(parent_path+config["local_storage"]["sound data"],"w",encoding="utf-8")
            soundDataJson.write(json.dumps(soundData))
            soundDataJson.close()
            os.remove(parent_path+config["local_storage"]["sound path"]+"/"+id+".mp3")
            alert_mss = "delete successfully ลบสำเร็จ"
        return HTMLResponse(redirect("/admin/edit"))
