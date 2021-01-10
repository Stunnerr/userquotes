import imgkit
import requests
import PIL
import os
from PIL import Image, ImageDraw
from .. import loader, utils


@loader.tds
class QuoteBuilderMod(loader.Module):
    """
    Generates quotes on userbot, without an API.
    """

    arrow = """
      <svg preserveAspectRatio="XMinYMin slice" height="12pt" width="12pt" viewBox="0 0 28 28" xmlns="http://www.w3.org/2000/svg">
      <path d="M27 28V0L0.707107 26.2929C0.077142 26.9229 0.523308 28 1.41421 28H27Z"></path>
      </svg>
    """
    html = """
      <!DOCTYPE html/>
      <html><head><meta charset="utf-8"/>
      <style>
    """
    wk_options = {
        "transparent":                  "",
        "enable-local-file-access":     "",
        "encoding":                     "UTF-8",
        "zoom":                         "3.0",
        "xvfb":                         ""
    }
    wk_avatar_options = {
        "width":      "512",
        "encoding":   "UTF-8",
        "height":     "512",
        "xvfb": ""
    }

    def create_without_name(self, text, rtext=None, rname=None):
        msg = '<div class="message">\n'
        if rtext != None and rname != None:
            msg += f'<div class="reply"><div class="rname">{rname}</div><div class="text">{rtext}</div></div>'
        msg += f'<div class="text">{text}</div></div>\n'
        return msg
        #raise NotImplementedError()

    def create_with_name(self, text, name, pic, num=0, rtext=None, rname=None):
        msg = '<div class="message">\n'
        msg += f'<div class="sender c{num}">{name}</div>\n'
        if rtext != None and rname != None:
            msg += f'<div class="reply"><div class="rname">{rname}</div><div class="text">{rtext}</div></div>'
        msg += f'<div class="text">{text}</div>'
        msg += f'<img src="{pic}" class="avatar">\n'
        msg += self.arrow
        msg += '</div>\n'
        return msg
        #raise NotImplementedError()

    def format_avatar(self, name, id):
        return self.avatar.replace("{name}", name[0]).replace("{num}", str(id))

    async def get_avatar(self, sender, name):
        avatar = "tempava.png"
        if sender and sender.photo:
            avatar = await self.client.download_profile_photo(sender)
        else:
            imgkit.from_string(self.format_avatar(name, sender.id if sender else 0),
                               output_path="tempava.png", options=self.wk_avatar_options)
        return avatar

    async def client_ready(self, client, db):
        self.avatar = requests.get(
            url="https://nivolog.ga/quotes/ava.html").text
        css = requests.get(url="https://nivolog.ga/quotes/quotes.css").text
        self.html += css
        self.html += "</style></head><body>\n"
        self.client = client

    async def quotecmd(self, message):
        """
        Quote this!
        """
        args = utils.get_args_raw(message.message).split()
        count = int(args[0]) - 1 if args else 0
        html = self.html
        client = self.client
        if not message.is_reply:
            return await message.edit("Reply to a message, retard")
        else:
            reply = await message.get_reply_message()
        await message.edit("Hacking Pentagon..")
        junkfiles = ["quote.png", "quote.webp", "quote.html"]

        # First message
        html += '<div class="message">\n'
        fwd = reply.fwd_from  # Entity getter
        fromid = None
        if fwd:
            if fwd.from_id:
                fromid = reply.forward.sender
            elif fwd.channel_id:
                fromid = reply.forward.chat
        else:
            fromid = reply.sender
        fromname = "No name"  # Name getter
        try:
            fromname = fromid.title
        except AttributeError:
            fromname = fwd.from_name if fwd and fwd.from_name else fromid.first_name
        rtext = None
        rname = None
        if reply.is_reply:
            tmpr = await reply.get_reply_message()
            rtext = "<br/>".join(tmpr.text.splitlines())
            rname = tmpr.sender.first_name
        text = "<br/>".join(reply.text.splitlines())
        prevsender = fromid
        pic = await self.get_avatar(fromid, fromname)
        junkfiles.append(pic)
        # Other messages
        messages = await client.get_messages(reply.chat, min_id=reply.id, limit=count, reverse=True)
        for msg in messages:
            # Match prev and cur message entities
            fwd = msg.fwd_from
            fromid = None  # Get entity
            if fwd:
                if fwd.from_id:
                    fromid = msg.forward.sender
                elif fwd.channel_id:
                    fromid = msg.forward.chat
            else:
                fromid = msg.sender
            if not (fromid == prevsender):  # Save prev message
                html += self.create_with_name(text, fromname, pic,
                                              fromid.id % 7 if fromid else 0, rtext, rname)
            else:
                html += self.create_without_name(text, rtext, rname)
            # Start creating cur message
            fromname = "No name"  # Get name
            try:
                fromname = fromid.title
            except AttributeError:
                fromname = fwd.from_name if fwd and fwd.from_name else fromid.first_name
            rtext = None
            rname = None
            if msg.is_reply:
                tmpr = await msg.get_reply_message()
                rtext = "<br/>".join(tmpr.text.splitlines())
                rname = tmpr.sender.first_name
            pic = await self.get_avatar(fromid, fromname)
            junkfiles.append(pic)
            text = "<br/>".join(msg.text.splitlines())
            prevsender = fromid
        html += self.create_with_name(text, fromname, pic,
                                      fromid.id % 7 if fromid else 0, rtext, rname)
        html += "</body></html>"
        open("quote.html", "w").write(html)
        try:
            imgkit.from_file("quote.html", "quote.png",
                             options=self.wk_options)
        except Exception as e:
            if not "ProtocolUnknownError" in str(e):
                raise e
        img = Image.open("quote.png").convert("RGBA")
        if (img.size[0] < 513 and img.size[1] < 513):
            cropimg = img
        else:
            cropimg = img.resize((512, int(
                float(img.size[1]) * float(512 / float(img.size[0])))), PIL.Image.ANTIALIAS)
        cropimg.save('quote.webp')
        client = reply.client
        await message.edit("Leaking your personal data..")
        if img.size[1] > 1024:
            await client.send_file(message.to_id, 'quote.png', reply_to=reply)
        else:
            await client.send_file(message.to_id, 'quote.webp', reply_to=reply)
        await message.edit("Removing OS..")
        for junk in junkfiles:
            os.remove(junk)
        await message.delete()
