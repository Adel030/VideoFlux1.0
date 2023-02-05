from config import Config
from telethon import events, Button
from helper_fns.Helper import USER_DATA, getbotuptime, new_user, get_details, clear_trash_list, process_checker, get_config, saveoptions, delete_trash, save_restart, get_logs_msg, gen_random_string
from helper_fns.Ruunung_Process import append_master_process, remove_master_process, get_master_process, remove_sub_process
from os.path import exists
from asyncio import sleep as asynciosleep
from os import execl
from sys import argv, executable
from helper_fns.Queue import get_queue
from helper_fns.Processor import start_process



#////////////////////////////////////Variables////////////////////////////////////#
sudo_users = Config.SUDO_USERS
Client = Config.client
LOGGER = Config.LOGGER
SAVE_TO_DATABASE = Config.SAVE_TO_DATABASE


#////////////////////////////////////Functions////////////////////////////////////#
async def init_user(event, userx):
    if userx not in sudo_users:
                    await event.reply("❌Not Authorized")
                    return False
    if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
    if userx not in get_queue():
        get_queue()[userx] = {}
        get_queue()[userx]['tasks'] = []
        get_queue()[userx]['started'] = False
    return True

async def get_ext(event):
    if "|" in event.message.message:
        ext = str(event.message.message.split('|')[-1]).replace('.', '').strip()
    else:
        ext = False
    return ext

async def get_dw_type(new_event):
    try:
        if new_event.message.media:
            return ["tg", False]
        else:
            return ["url", False]
    except:
        return ["tg", False]

async def get_url_from_message(new_event):
        if new_event.message.file:
            return False
        else:
            return str(new_event.message.message)


#////////////////////////////////////Telethon Functions////////////////////////////////////#

###############------Mention_User------###############
def get_mention(event):
    return "["+event.message.sender.first_name+"](tg://user?id="+str(event.message.sender.id)+")"

###############------Ask_Media------###############
async def ask_media(event, user_id, userx, detailed_message, keywords, message, timeout, mtype, queue_task):
    async with Client.conversation(user_id) as conv:
            handle = conv.wait_event(events.NewMessage(chats=user_id, incoming=True, from_users=[userx], func=lambda e: e.message.file or str(e.message.message) in keywords or str(e.message.message).startswith("http")), timeout=timeout)
            if not queue_task:
                msg = f"*️⃣ {str(message)} [{str(timeout)} secs]"
            else:
                msg = f"*️⃣ {str(message)} [{str(timeout)} secs]\n\n#️⃣Task Queuing Is ON\n🔶Queued Tasks : {str(len(get_queue()[userx]['tasks']))}"
            if not detailed_message:
                ask = await event.reply(msg)
            else:
                ask = await event.reply(f'{msg} \n\n{str(detailed_message)}')
            try:
                new_event = await handle
            except Exception as e:
                await ask.reply('🔃Timed Out! Tasked Has Been Cancelled.')
                LOGGER.info(str(e))
                return False
            if new_event.message.file:
                if not str(new_event.message.file.mime_type).startswith(mtype):
                    await new_event.reply(f'❗[{str(new_event.message.file.mime_type)}] This is not a valid file.')
                    return False
                return new_event
            elif new_event.message.message:
                if str(new_event.message.message)=='stop':
                    await ask.reply('✅Task Stopped')
                    return "cancelled"
                elif str(new_event.message.message)=='pass':
                    await ask.reply('✅Task Passed')
                    return "passed"
                elif str(new_event.message.message).startswith("http"):
                    return new_event
                else:
                    await ask.reply(f'❗You already started a task, now send {str(new_event.message.message)} command again.')
                    return "cancelled"


#////////////////////////////////////Bot_Commands////////////////////////////////////#

###############------Start_Message------###############
@Client.on(events.NewMessage(incoming=True, pattern='/start'))
async def _batch(event):
    text = f"Hi {get_mention(event)}, I Am Alive."
    await event.reply(text, buttons=[
    [Button.url('⭐ Bot By 𝚂𝚊𝚑𝚒𝚕 ⭐', 'https://t.me/nik66')],
    [Button.url('❤ Join Channel ❤', 'https://t.me/nik66x')]
])
    return

###############------Bot_UpTime------###############
@Client.on(events.NewMessage(incoming=True, pattern='/time'))
async def _timecmd(event):
    user_id = event.message.chat.id
    userx = event.message.sender.id
    if userx in sudo_users:
        await event.reply(f'♻Bot Is Alive For {getbotuptime()}')
    else:
        await event.reply(f"❌Only Authorized Users Can Use This Command")
    return

###############------Cancel Process------###############
@Client.on(events.NewMessage(incoming=True, pattern='/cancel'))
async def _cancel(event):
  user_id = event.message.chat.id
  userx = event.message.sender.id
  if userx in sudo_users:
        commands = event.message.message.split(' ')
        if len(commands)==3:
                processx = commands[1]
                process_id = commands[2]
                try:
                        if processx=='sp':
                                        dresult = remove_sub_process(process_id)
                                        if dresult:
                                            await event.reply(f'✅Successfully Cancelled.')
                                        else:
                                            await event.reply(f'❗No Running Processs With This ID')
                        elif processx=='mp':
                                        dresult =remove_master_process(process_id)
                                        if dresult:
                                            await event.reply(f'✅Successfully Cancelled.')
                                        else:
                                            await event.reply(f'❗No Running Processs With This ID')
                except Exception as e:
                        await event.reply(str(e))
                return
        else:
                await event.reply(f'❗Give Me Process ID To Cancel.')
  else:
        await event.reply(f"❌Only Authorized Users Can Use This Command")
        return


###############------Settings------###############
@Client.on(events.NewMessage(incoming=True, pattern='/settings'))
async def _settings(event):
        userx = event.message.sender.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        text = f"⚙ Hi {get_mention(event)} Choose Your Settings"
        await event.reply(text, buttons=[
        [Button.inline('#️⃣ General', 'general_settings')],
        [Button.inline('📝 Progress Bar', 'progress_settings')],
        [Button.inline('🏮 Compression', 'compression_settings')],
        [Button.inline('⭕Close Settings', 'close_settings')]
    ])
        return


###############------Compress------###############
@Client.on(events.NewMessage(incoming=True, pattern='/compress'))
async def _compress(event):
    user_id = event.message.chat.id
    userx = event.message.sender.id
    validate = await init_user(event, userx)
    if not validate:
        return
    ext = await get_ext(event)
    queue_task = get_queue()[userx]['started']
    new_event = await ask_media(event, user_id, userx, get_details("compress", userx, True), ["/compress", "stop"], "Send Video or URL", 120, "video/", queue_task)
    if new_event and new_event not in ["cancelled"]:
            url = await get_url_from_message(new_event)
            trash_list = []
            await start_process(Client, new_event, user_id, userx, False, queue_task, url, ext, 'compress', False, "1/1", False, False, trash_list)
            await clear_trash_list(trash_list)
            if not queue_task:
                await asynciosleep(1)
                await event.reply("✅Task Completed Successfully")
            return


###############------Start/Process_Queue------###############
@Client.on(events.NewMessage(incoming=True, pattern='/queue'))
async def _queue(event):
    user_id = event.message.chat.id
    userx = event.message.sender.id
    if userx not in sudo_users:
                    await event.reply("❌Not Authorized")
                    return
    if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
    if userx not in get_queue():
        get_queue()[userx] = {}
        get_queue()[userx]['tasks'] = []
        get_queue()[userx]['started'] = False
    if not get_queue()[userx]['started']:
        get_queue()[userx]['started'] = True
        await event.reply("✅Queuing Has Started, Now You Can Add Task To Queue.")
        return
    else:
        total_queue = len(get_queue()[userx]['tasks'])
        if total_queue:
            tasks = get_queue()[userx]['tasks']
            get_queue()[userx]['started'] = False
            get_queue()[userx]['tasks'] = []
            p = 1
            process_id = gen_random_string(10)
            append_master_process(process_id)
            for queue_data in tasks:
                trash_list = []
                try:
                    await start_process(Client, None, user_id, userx, None, False, None, None, None, queue_data, f"{str(p)}/{str(total_queue)}", process_id, [[process_id, get_master_process()]], trash_list)
                except Exception as e:
                    print(e)
                    LOGGER.info(str(e))
                await clear_trash_list(trash_list)
                if not (await process_checker([[process_id, get_master_process()]])):
                    break
                p+=1
            await event.reply("✅Task Completed Successfully")
            return
        else:
            await event.reply("❗Queue Tasks Is Empty.")
            return


###############------Clear_Queue------###############
@Client.on(events.NewMessage(incoming=True, pattern='/clearqueue'))
async def _clearqueue(event):
    userx = event.message.sender.id
    if userx not in sudo_users:
                    await event.reply("❌Not Authorized")
                    return
    if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
    if userx not in get_queue():
        get_queue()[userx] = {}
        get_queue()[userx]['tasks'] = []
        get_queue()[userx]['started'] = False
    if not get_queue()[userx]['started']:
        await event.reply("❗Queuing Is Not Started Yet.")
        return
    else:
        get_queue()[userx]['tasks'] = []
        await event.reply("✅Successfully Cleared Queued Tasks")
        return


###############------Terminate_Queue------###############
@Client.on(events.NewMessage(incoming=True, pattern='/terminatequeue'))
async def _terminatequeue(event):
    userx = event.message.sender.id
    if userx not in sudo_users:
                    await event.reply("❌Not Authorized")
                    return
    if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
    if userx not in get_queue():
        get_queue()[userx] = {}
        get_queue()[userx]['tasks'] = []
        get_queue()[userx]['started'] = False
    if not get_queue()[userx]['started']:
        await event.reply("❗Queuing Is Not Started Yet.")
        return
    else:
        get_queue()[userx]['started'] = False
        get_queue()[userx]['tasks'] = []
        await event.reply("✅Successfully Terminated Queuing.")
        return


###############------Clear_One_Queue------###############
@Client.on(events.NewMessage(incoming=True, pattern='/clearonequeue'))
async def _clearonequeue(event):
    user_id = event.message.chat.id
    userx = event.message.sender.id
    if userx not in sudo_users:
                    await event.reply("❌Not Authorized")
                    return
    if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
    if userx not in get_queue():
        get_queue()[userx] = {}
        get_queue()[userx]['tasks'] = []
        get_queue()[userx]['started'] = False
    if not get_queue()[userx]['started']:
        await event.reply("❗Queuing Is Not Started Yet.")
        return
    else:
        total_queue = len(get_queue()[userx]['tasks'])
        if total_queue:
            q = 1
            msg = f"🔶Queued Tasks : {str(total_queue)}\n\n*️⃣ Send Task Index\n"
            for queue_data in get_queue()[userx]['tasks']:
                msg+= f"`{str(q)}` - {str(queue_data['file_name'])}\n"
                q+=1
            async with Client.conversation(user_id) as conv:
                handle = conv.wait_event(events.NewMessage(chats=user_id, incoming=True, from_users=[userx], func=lambda e: int(e.message.message)), timeout=60)
                ask = await event.reply(f'{str(msg)}')
                try:
                    new_event = await handle
                except Exception as e:
                    await ask.reply('🔃Timed Out! Tasked Has Been Cancelled.')
                    print(e)
                    return
                try:
                    index = int(new_event.message.message)-1
                    del get_queue()[userx]['tasks'][index]
                    q = 1
                    msg = ''
                    for queue_data in get_queue()[userx]['tasks']:
                        msg+= f"`{str(q)}` - {str(queue_data['file_name'])}\n"
                        q+=1
                    await new_event.reply(f"✅Successfully Cleared Task\n\n🔶Queued Tasks : {str(len(get_queue()[userx]['tasks']))}\n\n{str(msg)}")
                except Exception as e:
                    await new_event.reply(f"❗{str(e)}")
                return
        else:
            await event.reply("❗Queue Tasks Is Empty.")
            return


###############------Get_Queued_Tasks------###############
@Client.on(events.NewMessage(incoming=True, pattern='/getqueue'))
async def _getqueue(event):
    user_id = event.message.chat.id
    userx = event.message.sender.id
    if userx not in sudo_users:
                    await event.reply("❌Not Authorized")
                    return
    if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
    if userx not in get_queue():
        get_queue()[userx] = {}
        get_queue()[userx]['tasks'] = []
        get_queue()[userx]['started'] = False
    if not get_queue()[userx]['started']:
        await event.reply("❗Queuing Is Not Started Yet.")
        return
    else:
        total_queue = len(get_queue()[userx]['tasks'])
        if total_queue:
            q = 1
            msg = f"🔶Queued Tasks : {str(total_queue)}\n\n"
            for queue_data in get_queue()[userx]['tasks']:
                msg+= f"`{str(q)}` - {str(queue_data['file_name'])}\n"
                q+=1
            await event.reply(msg)
            return
        else:
            await event.reply("❗Queue Tasks Is Empty.")
            return


###############------Save_Rclone_Config------###############
@Client.on(events.NewMessage(incoming=True, pattern='/saveconfig'))
async def _saverclone(event):
        userx = event.message.sender.id
        user_id = event.message.chat.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        r_config = f'./userdata/{str(userx)}_rclone.conf'
        check_config = exists(r_config)
        if check_config:
                text = f"Rclone Config Already Present\n\nSend Me New Config To Replace."
        else:
                text = f"Rclone Config Not Present\n\nSend Me Config To Save."
        new_event = await ask_media(event, user_id, userx, False, ["/saveconfig", "stop"], text, 60, "text/", False)
        if new_event and new_event not in ["cancelled"]:
            await Client.download_media(new_event.message, r_config)
            accounts = await get_config(r_config)
            if not accounts:
                await delete_trash(r_config)
                await new_event.reply("❌Invalid Config File Or Empty Config File.")
                return
            await saveoptions(userx, 'drive_name', accounts[0], SAVE_TO_DATABASE)
            await new_event.reply(f"✅Config Saved Successfully\n\n🔶Using {str(USER_DATA()[userx]['drive_name'])} Drive For Uploading.")
        return


###############------Renew------###############
@Client.on(events.NewMessage(incoming=True, pattern='/renew'))
async def _renew(event):
        userx = event.message.sender.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        await event.reply("*️⃣Are you sure?\n\n🚫 This will delete all your downloads and saved watermark locally 🚫", buttons=[
                [Button.inline('Yes 🚫', 'renew_True')],
                [Button.inline('No 😓', 'renew_False')]
            ])
        return


###############------Restart------###############
@Client.on(events.NewMessage(incoming=True, pattern='/restart'))
async def _restart(event):
        userx = event.message.sender.id
        user_id = event.message.chat.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        reply = await event.reply("♻Restarting...")
        if SAVE_TO_DATABASE:
            await save_restart(user_id, reply.id)
        execl(executable, executable, *argv)


###############------Add_SUDO------###############
@Client.on(events.NewMessage(incoming=True, pattern='/addsudo'))
async def _addsudo(event):
        userx = event.message.sender.id
        user_id = event.message.chat.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        async with Client.conversation(user_id) as conv:
                handle = conv.wait_event(events.NewMessage(chats=user_id, incoming=True, from_users=[userx], func=lambda e: int(e.message.message)), timeout=60)
                ask = await event.reply(f'*️⃣Send User Numerical ID')
                try:
                    new_event = await handle
                except Exception as e:
                    await ask.reply('🔃Timed Out! Tasked Has Been Cancelled.')
                    print(e)
                    return
        ask_id = int(new_event.message.message)
        if ask_id not in sudo_users:
            sudo_users.append(ask_id)
            await new_event.reply(f"✅Successfully Added User To Sudo Users\n\n{str(sudo_users)}")
        else:
            await new_event.reply(f"❗User Already In Sudo Users\n\n{str(sudo_users)}")
        return


###############------Delete_SUDO------###############
@Client.on(events.NewMessage(incoming=True, pattern='/delsudo'))
async def _delsudo(event):
        userx = event.message.sender.id
        user_id = event.message.chat.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        async with Client.conversation(user_id) as conv:
                handle = conv.wait_event(events.NewMessage(chats=user_id, incoming=True, from_users=[userx], func=lambda e: int(e.message.message)), timeout=60)
                ask = await event.reply(f'*️⃣Send User Numerical ID')
                try:
                    new_event = await handle
                except Exception as e:
                    await ask.reply('🔃Timed Out! Tasked Has Been Cancelled.')
                    print(e)
                    return
        ask_id = int(new_event.message.message)
        if ask_id in sudo_users:
            sudo_users.remove(ask_id)
            await new_event.reply(f"✅Successfully Removed User From Sudo Users\n\n{str(sudo_users)}")
        else:
            await new_event.reply(f"❗User Not In Sudo Users\n\n{str(sudo_users)}")
        return
    

###############------Get_SUDO------###############
@Client.on(events.NewMessage(incoming=True, pattern='/getsudo'))
async def _getsudo(event):
        userx = event.message.sender.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        await event.reply(f"{str(sudo_users)}")
        return
    

###############------Get_Logs_Message------###############
@Client.on(events.NewMessage(incoming=True, pattern='/log'))
async def _log(event):
        userx = event.message.sender.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        log_file = "Logging.txt"
        if exists(log_file):
                await event.reply(str(get_logs_msg(log_file)))
        else:
            await event.reply("❗Log File Is Not Found")
        return


###############------Get_Log_File------###############
@Client.on(events.NewMessage(incoming=True, pattern='/logs'))
async def _logs(event):
        userx = event.message.sender.id
        user_id = event.message.chat.id
        if userx not in sudo_users:
                        await event.reply("❌Not Authorized")
                        return
        if userx not in USER_DATA():
                await new_user(userx, SAVE_TO_DATABASE)
        log_file = "Logging.txt"
        if exists(log_file):
            await Client.send_file(user_id, file=log_file, allow_cache=False)
        else:
            await event.reply("❗Log File Is Not Found")
        return