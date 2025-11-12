package com.github.catvod.spider;

import android.content.Context;
import android.text.TextUtils;
import com.github.catvod.crawler.Spider;
import com.github.catvod.spider.merge.D.a;
import com.github.catvod.spider.merge.G.i;
import com.github.catvod.spider.merge.a.C0632a;
import com.github.catvod.spider.merge.b.C0642h;
import com.github.catvod.spider.merge.b.C0645k;
import com.github.catvod.spider.merge.b.u;
import com.github.catvod.spider.merge.b.x;
import com.github.catvod.spider.merge.c.C0646a;
import com.github.catvod.spider.merge.c.C0648c;
import com.github.catvod.spider.merge.c.C0650e;
import com.github.catvod.spider.merge.k.C0669b;
import com.github.catvod.spider.merge.m.C0686I;
import java.net.URLEncoder;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.UUID;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.json.JSONArray;
import org.json.JSONObject;

public class Web1905 extends Spider {
    private static final Pattern a = Pattern.compile("play/(.*?).sh");

    private String a(String str) {
        HashMap c = C0642h.c("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36", "Referer", "https://www.1905.com");
        c.put("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7");
        return C0669b.l(str, c);
    }

    public String categoryContent(String str, String str2, boolean z, HashMap<String, String> hashMap) {
        Iterator it = a.a(a("https://www.1905.com/vod/list/" + str + "/o3p" + str2 + ".html")).n0("n_2".equals(str) ? "div.mod > div > a" : "section.search-list > div > a").iterator();
        ArrayList arrayList = new ArrayList();
        while (it.hasNext()) {
            i iVar = (i) it.next();
            String d = iVar.d("href");
            Matcher matcher = a.matcher(d);
            if (matcher.find()) {
                d = matcher.group(1);
            }
            C0645k.b(d, iVar.d("title"), iVar.n0("img").a("src"), iVar.n0("p").c(), arrayList);
        }
        return C0642h.a(str2, new C0648c(), 0, 0, 0, arrayList);
    }

    public String detailContent(List<String> list) {
        String str = list.get(0);
        JSONObject jSONObject = new JSONObject(a(u.a("https://www.1905.com/api/content/?m=Vod&a=getVodSidebar&id=", str, "&fomat=json")));
        C0650e eVar = new C0650e();
        eVar.j(str);
        String optString = jSONObject.optString("title");
        eVar.k(optString);
        eVar.l(jSONObject.optString("thumb"));
        eVar.o(jSONObject.optString("commendreason"));
        eVar.h(jSONObject.optString("description"));
        eVar.i(jSONObject.optString("direct"));
        eVar.f(jSONObject.optString("starring"));
        ArrayList arrayList = new ArrayList();
        arrayList.add(optString + "$" + str);
        JSONArray optJSONArray = jSONObject.optJSONObject("info").optJSONArray("series_data");
        for (int i = 0; i < optJSONArray.length(); i++) {
            JSONObject optJSONObject = optJSONArray.optJSONObject(i);
            arrayList.add(optJSONObject.optString("title") + "$" + optJSONObject.optString("contentid"));
        }
        eVar.m("1905");
        eVar.n(TextUtils.join("#", arrayList));
        return C0648c.m(eVar);
    }

    public String homeContent(boolean z) {
        ArrayList arrayList = new ArrayList();
        List asList = Arrays.asList(new String[]{"n_1", "n_1_c_922", "n_2", "c_927", "n_1_c_586", "n_1_c_178", "n_1_c_1024", "n_1_c_1053"});
        List asList2 = Arrays.asList(new String[]{"电影", "微电影", "系列电影", "记录片", "晚会", "独家", "综艺", "体育"});
        for (int i = 0; i < asList.size(); i++) {
            arrayList.add(new C0646a((String) asList.get(i), (String) asList2.get(i), (String) null));
        }
        return C0648c.p(arrayList, new ArrayList());
    }

    public void init(Context context, String str) {
        Web1905.super.init(context, str);
    }

    public String playerContent(String str, String str2, List<String> list) {
        String str3;
        long currentTimeMillis = System.currentTimeMillis() / 1000;
        long j = 600 + currentTimeMillis;
        String uuid = UUID.randomUUID().toString();
        String str4 = "";
        String substring = uuid.replace("-", str4).substring(5, 20);
        String k = C0686I.k(String.format("cid=%s&expiretime=%d&nonce=%d&page=%s&playerid=%s&type=hls&uuid=%s.dde3d61a0411511d", new Object[]{str2, Long.valueOf(j), Long.valueOf(currentTimeMillis), u.a("https://www.1905.com/vod/play/", str2, ".shtml").replace(":", "%3A").replace("/", "%2F"), substring, uuid}));
        StringBuilder sb = new StringBuilder();
        sb.append("https://profile.m1905.com/mvod/getVideoinfo.php?nonce=");
        sb.append(currentTimeMillis);
        sb.append("&expiretime=");
        sb.append(j);
        sb.append("&cid=");
        sb.append(str2);
        x.a(sb, "&uuid=", uuid, "&playerid=", substring);
        x.a(sb, "&page=https%3A%2F%2Fwww.1905.com%2Fvod%2Fplay%2F", str2, ".shtml&type=hls&signature=", k);
        sb.append("&callback=");
        JSONObject optJSONObject = new JSONObject(a(sb.toString()).replace("(", str4).replace(")", str4)).optJSONObject("data");
        Iterator<String> keys = optJSONObject.optJSONObject("sign").keys();
        ArrayList arrayList = new ArrayList();
        while (keys.hasNext()) {
            arrayList.add(keys.next());
        }
        if (arrayList.contains("uhd")) {
            str3 = optJSONObject.optJSONObject("sign").optJSONObject("uhd").optString("sign");
            str4 = "uhd";
        } else if (arrayList.contains("hd")) {
            str3 = optJSONObject.optJSONObject("sign").optJSONObject("hd").optString("sign");
            str4 = "hd";
        } else if (arrayList.contains("sd")) {
            str3 = optJSONObject.optJSONObject("sign").optJSONObject("sd").optString("sign");
            str4 = "sd";
        } else {
            str3 = str4;
        }
        String a2 = u.a(optJSONObject.optJSONObject("quality").optJSONObject(str4).optString("host"), str3, optJSONObject.optJSONObject("path").optJSONObject(str4).optString("path"));
        C0648c cVar = new C0648c();
        cVar.k(0);
        cVar.u(a2);
        return cVar.toString();
    }

    public String searchContent(String str, boolean z) {
        StringBuilder a2 = C0632a.a("https://www.1905.com/search/index-p-type-all-q-");
        a2.append(URLEncoder.encode(str));
        a2.append(".html");
        Iterator it = a.a(a(a2.toString())).n0("div.movie_box > div > div").iterator();
        ArrayList arrayList = new ArrayList();
        while (it.hasNext()) {
            i iVar = (i) it.next();
            String a3 = iVar.n0("div > ul > li.paly-tab-icon > a").a("href");
            if (!TextUtils.isEmpty(a3)) {
                Matcher matcher = a.matcher(a3);
                if (matcher.find()) {
                    a3 = matcher.group(1);
                }
                C0645k.b(a3, iVar.n0("div > div.movie-pic > a > img").a("alt"), iVar.n0("div > div.movie-pic > a > img").a("src"), "", arrayList);
            }
        }
        return C0648c.n(arrayList);
    }
}
