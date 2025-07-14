const MAPPING_URL = "https://raw.githubusercontent.com/yenkj/epg/main/epg/channel-map.json";
const LOGO_BASE_URL = "https://raw.githubusercontent.com/yenkj/epg/main/logo/";

const DEFAULT_EPG = [
  { start: "00:00", desc: "", end: "02:00", title: "精彩节目" },
  { start: "02:00", desc: "", end: "04:00", title: "精彩节目" },
  { start: "04:00", desc: "", end: "06:00", title: "精彩节目" },
  { start: "06:00", desc: "", end: "08:00", title: "精彩节目" },
  { start: "08:00", desc: "", end: "10:06", title: "精彩节目" },
  { start: "10:06", desc: "", end: "12:00", title: "精彩节目" },
  { start: "12:00", desc: "", end: "14:00", title: "精彩节目" },
  { start: "14:00", desc: "", end: "16:00", title: "精彩节目" },
  { start: "16:00", desc: "", end: "18:00", title: "精彩节目" },
  { start: "18:00", desc: "", end: "19:00", title: "精彩节目" },
  { start: "19:00", desc: "", end: "20:00", title: "精彩节目" },
  { start: "20:00", desc: "", end: "22:00", title: "精彩节目" },
  { start: "22:00", desc: "", end: "23:59", title: "精彩节目" }
];

function formatTime(datetime) {
  const hh = datetime.slice(8, 10);
  const mm = datetime.slice(10, 12);
  return `${hh}:${mm}`;
}

function parseEPG(xml, dayPrefix, mode = "today") {
  const result = [];
  const programmeRegex = /<programme[^>]+?start="([^"]+)" stop="([^"]+)"[^>]*>([\s\S]*?)<\/programme>/g;
  let match;

  while ((match = programmeRegex.exec(xml))) {
    const [_, startRaw, endRaw, content] = match;

    if (mode === "today" && !startRaw.startsWith(dayPrefix)) continue;
    if (mode === "carry" && !endRaw.startsWith(dayPrefix)) continue;

    const titleMatch = /<title[^>]*>([\s\S]*?)<\/title>/.exec(content);
    const descMatch = /<desc[^>]*>([\s\S]*?)<\/desc>/.exec(content);

    result.push({
      start: formatTime(startRaw),
      end: formatTime(endRaw),
      title: titleMatch ? titleMatch[1].trim() : "",
      desc: descMatch ? descMatch[1].trim() : ""
    });
  }

  return result;
}

export default {
  async fetch(request, env, ctx) {
    const url = new URL(request.url);
    const pathname = url.pathname;

    // ===== Logo 路由 =====
    if (pathname.startsWith("/logo/")) {
      const filename = pathname.replace("/logo/", "");
      const logoUrl = LOGO_BASE_URL + filename;

      try {
        const logoRes = await fetch(logoUrl, { cf: { cacheTtl: 60 } });
        if (!logoRes.ok) return new Response("Logo not found", { status: 404 });

        const ext = filename.split(".").pop().toLowerCase();
        const contentTypeMap = {
          png: "image/png",
          jpg: "image/jpeg",
          jpeg: "image/jpeg",
          webp: "image/webp",
          svg: "image/svg+xml"
        };

        const contentType = contentTypeMap[ext] || "application/octet-stream";

        return new Response(await logoRes.arrayBuffer(), {
          headers: {
            "Content-Type": contentType,
            "Cache-Control": "public, max-age=60",
            "Access-Control-Allow-Origin": "*"
          }
        });
      } catch (err) {
        return new Response("Error loading logo", { status: 500 });
      }
    }

    // ===== EPG 路由 =====
    try {
      const lang = url.searchParams.get("lang") || "zh-hans";
      const timezone = url.searchParams.get("timezone") || "QXNpYS9TaGFuZ2hhaQ==";

      const rawDate = url.searchParams.get("date");
      const normalizedDate = rawDate ? rawDate.replace(/-/g, "") : "";
      const formattedDate = normalizedDate.length === 8
        ? `${normalizedDate.slice(0, 4)}-${normalizedDate.slice(4, 6)}-${normalizedDate.slice(6, 8)}`
        : "";

      const nameRaw = url.searchParams.get("ch") || "";
      const name = decodeURIComponent(nameRaw.trim());

      const mappingRes = await fetch(MAPPING_URL, { cf: { cacheTtl: 60 } });
      if (!mappingRes.ok) throw new Error("无法加载频道映射文件");
      const channelMap = await mappingRes.json();

      let realId = null;
      for (const [id, names] of Object.entries(channelMap)) {
        if (Array.isArray(names) && names.includes(name)) {
          realId = id;
          break;
        }
      }

      let epg_data = [];

      if (realId) {
        // === 获取今天的 EPG ===
        const epgUrlToday = `https://epg.pw/api/epg.xml?lang=${lang}&timezone=${timezone}&date=${normalizedDate}&channel_id=${realId}`;
        const epgResToday = await fetch(epgUrlToday);
        const todayXml = await epgResToday.text();
        const todayList = parseEPG(todayXml, normalizedDate, "today");

        // === 获取昨天的跨天节目 ===
        const prevDate = new Date(`${formattedDate}T00:00:00`);
        prevDate.setDate(prevDate.getDate() - 1);
        const prevDateStr = prevDate.toISOString().slice(0, 10).replace(/-/g, "");
        const epgUrlPrev = `https://epg.pw/api/epg.xml?lang=${lang}&timezone=${timezone}&date=${prevDateStr}&channel_id=${realId}`;
        const epgResPrev = await fetch(epgUrlPrev);
        const prevXml = await epgResPrev.text();
        const carryOverList = parseEPG(prevXml, normalizedDate, "carry");

        // === 判断是否添加跨天节目 ===
        const shouldIncludeCarryOver = (
          carryOverList.length > 0 &&
          !(todayList.length > 0 && todayList[0].start === "00:00")
        );

        if (shouldIncludeCarryOver) {
          if (todayList.length > 0) {
            carryOverList[0].start = "00:00";               // ✅ 设置 start 为 00:00
            carryOverList[0].end = todayList[0].start;      // ✅ 设置 end 为今天第一节目开始时间
          }
          epg_data.push(carryOverList[0]); // 只保留最后一个跨天节目
        }

        epg_data.push(...todayList);
      }

      const useDefault = !realId || epg_data.length === 0;

      const responseJson = {
        date: formattedDate,
        channel_name: name,
        url: "epg.199301.dpdns.org",
        epg_data: useDefault ? DEFAULT_EPG : epg_data
      };

      return new Response(JSON.stringify(responseJson, null, 2), {
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        }
      });
    } catch (e) {
      return new Response(JSON.stringify({
        date: "",
        channel_name: "未知频道",
        url: "epg.199301.dpdns.org",
        epg_data: DEFAULT_EPG
      }, null, 2), {
        status: 200,
        headers: {
          "Content-Type": "application/json; charset=utf-8",
          "Access-Control-Allow-Origin": "*"
        }
      });
    }
  }
};
