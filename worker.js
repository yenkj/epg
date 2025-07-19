const MAPPING_URL = "https://raw.githubusercontent.com/yenkj/epg/main/epg/channel-map.json";
const LOGO_BASE_URL = "https://raw.githubusercontent.com/yenkj/epg/main/logo/";
const EPG_XML_URL = "https://raw.githubusercontent.com/yenkj/epg/main/epg.xml";
const BOSS_XML_URL = "https://raw.githubusercontent.com/yenkj/epg/main/boss.xml";

const DEFAULT_EPG = [
  { start: "00:00", end: "02:00", title: "精彩节目", desc: "" },
  { start: "02:00", end: "04:00", title: "精彩节目", desc: "" },
  { start: "04:00", end: "06:00", title: "精彩节目", desc: "" },
  { start: "06:00", end: "08:00", title: "精彩节目", desc: "" },
  { start: "08:00", end: "10:00", title: "精彩节目", desc: "" },
  { start: "10:00", end: "12:00", title: "精彩节目", desc: "" },
  { start: "12:00", end: "14:00", title: "精彩节目", desc: "" },
  { start: "14:00", end: "16:00", title: "精彩节目", desc: "" },
  { start: "16:00", end: "18:00", title: "精彩节目", desc: "" },
  { start: "18:00", end: "20:00", title: "精彩节目", desc: "" },
  { start: "20:00", end: "22:00", title: "精彩节目", desc: "" },
  { start: "22:00", end: "23:59", title: "精彩节目", desc: "" }
];

// 解析时间字符串，形如 20250718000000 +0800，返回 HH:mm
function formatTime(datetime) {
  return `${datetime.slice(8, 10)}:${datetime.slice(10, 12)}`;
}

// 解析 epg.pw API 返回的 XML，mode 用来筛选当天或跨日节目
function parseEPG(xml, dayPrefix, mode = "today") {
  const result = [];
  const regex = /<programme[^>]+?start="([^"]+)" stop="([^"]+)"[^>]*>([\s\S]*?)<\/programme>/g;
  let match;

  while ((match = regex.exec(xml))) {
    const [_, start, end, content] = match;

    // 根据 mode 过滤：today 用 start 开头匹配，carry 用 end 开头匹配
    if (mode === "today" && !start.startsWith(dayPrefix)) continue;
    if (mode === "carry" && !end.startsWith(dayPrefix)) continue;

    const title = /<title[^>]*>([\s\S]*?)<\/title>/.exec(content)?.[1]?.trim() || "";
    const desc = /<desc[^>]*>([\s\S]*?)<\/desc>/.exec(content)?.[1]?.trim() || "";

    result.push({ start: formatTime(start), end: formatTime(end), title, desc });
  }

  return result;
}

// 解析 boss.xml 文件中的节目，筛选当天相关的，返回结构和 parseEPG 一致
async function parseBossXML(xml, dayPrefix) {
  const result = [];
  const regex = /<programme[^>]+start="([^"]+)" stop="([^"]+)" channel="([^"]+)"[^>]*>([\s\S]*?)<\/programme>/g;
  let match;

  while ((match = regex.exec(xml))) {
    const [_, start, stop, channel, content] = match;

    if (!start.startsWith(dayPrefix)) continue;

    const titleMatch = /<title>([\s\S]*?)<\/title>/.exec(content);
    const descMatch = /<desc>([\s\S]*?)<\/desc>/.exec(content);

    const title = titleMatch ? titleMatch[1].trim() : "";
    const desc = descMatch ? descMatch[1].trim() : "";

    result.push({
      start: formatTime(start),
      end: formatTime(stop),
      title,
      desc,
      channel
    });
  }
  return result;
}

// 兼容性获取日期参数函数，支持 ?date=xxx 或 ?xxx（第二参数是日期）
function getDateFromUrlParams(searchParams) {
  if (searchParams.has("date")) {
    return searchParams.get("date");
  }
  const entries = [...searchParams.entries()];
  if (entries.length > 1) {
    const secondValue = entries[1][1];
    if (/^\d{8}$/.test(secondValue) || /^\d{4}-\d{2}-\d{2}$/.test(secondValue)) {
      return secondValue;
    }
  }
  return null;
}

export default {
  async fetch(request, env, ctx) {
    // ===== 新增：获取北京时间日期 =====
    function getBeijingDateString() {
      return new Intl.DateTimeFormat("en-CA", {
        timeZone: "Asia/Shanghai",
        year: "numeric",
        month: "2-digit",
        day: "2-digit"
      }).format(new Date());
    }
    // ===============================

    const url = new URL(request.url);
    const pathname = url.pathname;

    // === /logo/xxx.png 静态转发 ===
    if (pathname.startsWith("/logo/")) {
      const filename = pathname.replace("/logo/", "");
      const logoUrl = LOGO_BASE_URL + filename;

      try {
        const res = await fetch(logoUrl, { cf: { cacheTtl: 300 } });
        if (!res.ok) return new Response("Logo not found", { status: 404 });

        const ext = filename.split(".").pop().toLowerCase();
        const types = {
          png: "image/png", jpg: "image/jpeg", jpeg: "image/jpeg",
          webp: "image/webp", svg: "image/svg+xml"
        };

        return new Response(await res.arrayBuffer(), {
          headers: {
            "Content-Type": types[ext] || "application/octet-stream",
            "Cache-Control": "public, max-age=300",
            "Access-Control-Allow-Origin": "*"
          }
        });
      } catch {
        return new Response("Error loading logo", { status: 500 });
      }
    }

    // === /epg.xml 代理转发 ===
    if (pathname === "/epg.xml") {
      try {
        const res = await fetch(EPG_XML_URL, { cf: { cacheTtl: 300 } });
        if (!res.ok) return new Response("EPG not found", { status: 404 });

        return new Response(await res.text(), {
          headers: {
            "Content-Type": "application/xml; charset=utf-8",
            "Cache-Control": "public, max-age=300",
            "Access-Control-Allow-Origin": "*"
          }
        });
      } catch {
        return new Response("Error loading epg.xml", { status: 500 });
      }
    }

    // === 主 API 逻辑 ===
    try {
      const chName = decodeURIComponent(url.searchParams.get("ch") || "").trim();

      // ===== 修改点：日期参数逻辑 =====
      // boss.xml 频道用北京时间，否则用UTC
      const bossChannels = ["龍華卡通台", "龍華日韓台", "美亞電影HD", "愛爾達體育2台", "LS-Time電影台"];

      let dateRaw = getDateFromUrlParams(url.searchParams);

      if (bossChannels.includes(chName)) {
        dateRaw = dateRaw || getBeijingDateString();
      } else {
        dateRaw = dateRaw || new Date().toISOString().slice(0, 10);
      }
      // ===============================

      const lang = url.searchParams.get("lang") || "zh-hans";
      const timezone = url.searchParams.get("timezone") || "QXNpYS9TaGFuZ2hhaQ==";

      const normalizedDate = dateRaw.replace(/-/g, "");
      const formattedDate = `${normalizedDate.slice(0, 4)}-${normalizedDate.slice(4, 6)}-${normalizedDate.slice(6, 8)}`;

      // 如果是 boss.xml 频道，特殊处理
      if (bossChannels.includes(chName)) {
        const bossRes = await fetch(BOSS_XML_URL);
        if (!bossRes.ok) throw new Error("Failed to fetch boss.xml");
        const bossXml = await bossRes.text();

        let bossEpgData = await parseBossXML(bossXml, normalizedDate);
        bossEpgData = bossEpgData.filter(prog => {
          if (chName === "龍華卡通台") return prog.channel === "ott-animation";
          if (chName === "龍華日韓台") return prog.channel === "ott-motion";
          if (chName === "美亞電影HD") return prog.channel === "meya-movie-hd";
          if (chName === "愛爾達體育2台") return prog.channel === "elta-sports-2";
          if (chName === "LS-Time電影台") return prog.channel === "LS-Time";
          return false;
        });

        return new Response(JSON.stringify({
          date: formattedDate,
          channel_name: chName,
          url: "epg.199301.dpdns.org",
          epg_data: bossEpgData.length ? bossEpgData : DEFAULT_EPG
        }, null, 2), {
          headers: {
            "Content-Type": "application/json; charset=utf-8",
            "Access-Control-Allow-Origin": "*"
          }
        });
      }

      // 其他频道，按原逻辑从 MAPPING_URL 和 epg.pw 获取数据
      const mapRes = await fetch(MAPPING_URL);
      const mapJson = await mapRes.json();

      let realId = null;
      for (const [id, aliases] of Object.entries(mapJson)) {
        if (aliases.includes(chName)) {
          realId = id;
          break;
        }
      }

      let epgData = [];

      if (realId) {
        // 请求当天节目单
        const todayUrl = `https://epg.pw/api/epg.xml?lang=${lang}&timezone=${timezone}&date=${normalizedDate}&channel_id=${realId}`;
        const todayRes = await fetch(todayUrl);
        const todayXml = await todayRes.text();
        const todayEPG = parseEPG(todayXml, normalizedDate, "today");

        // 请求前一天节目单，用于拼接跨日节目
        const prevDate = new Date(`${formattedDate}T00:00:00`);
        prevDate.setDate(prevDate.getDate() - 1);
        const prevDateStr = prevDate.toISOString().slice(0, 10).replace(/-/g, "");
        const prevUrl = `https://epg.pw/api/epg.xml?lang=${lang}&timezone=${timezone}&date=${prevDateStr}&channel_id=${realId}`;
        const prevRes = await fetch(prevUrl);
        const prevXml = await prevRes.text();
        const carryEPG = parseEPG(prevXml, normalizedDate, "carry");

        // 拼接跨日节目，保证00:00开头节目无断层
        if (
          carryEPG.length &&
          (!todayEPG.length || todayEPG[0].start !== "00:00")
        ) {
          carryEPG[0].start = "00:00";
          carryEPG[0].end = todayEPG[0]?.start || "01:00";
          epgData.push(carryEPG[0]);
        }

        epgData.push(...todayEPG);
      }

      return new Response(JSON.stringify({
        date: formattedDate,
        channel_name: chName,
        url: "epg.199301.dpdns.org",
        epg_data: epgData.length ? epgData : DEFAULT_EPG
      }, null, 2), {
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        }
      });
    } catch {
      return new Response(JSON.stringify({
        date: "",
        channel_name: "未知频道",
        url: "epg.199301.dpdns.org",
        epg_data: DEFAULT_EPG
      }, null, 2), {
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }
  }
};
