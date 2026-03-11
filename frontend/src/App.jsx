import { useState, useEffect, useCallback } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8000";

// ── 팀 약어 목록 ─────────────────────────────────────────
const TEAMS = [
  { abbr:"BOS", name:"Boston Celtics",        logo:"🍀", color:"#007A33", conf:"East" },
  { abbr:"CLE", name:"Cleveland Cavaliers",    logo:"⚔️", color:"#6F263D", conf:"East" },
  { abbr:"NYK", name:"New York Knicks",        logo:"🗽", color:"#006BB6", conf:"East" },
  { abbr:"IND", name:"Indiana Pacers",         logo:"🏎️", color:"#002D62", conf:"East" },
  { abbr:"MIL", name:"Milwaukee Bucks",        logo:"🦌", color:"#00471B", conf:"East" },
  { abbr:"MIA", name:"Miami Heat",             logo:"🔥", color:"#98002E", conf:"East" },
  { abbr:"OKC", name:"OKC Thunder",            logo:"⚡", color:"#007AC1", conf:"West" },
  { abbr:"HOU", name:"Houston Rockets",        logo:"🚀", color:"#CE1141", conf:"West" },
  { abbr:"DEN", name:"Denver Nuggets",         logo:"⛏️", color:"#4FA3E0", conf:"West" },
  { abbr:"DAL", name:"Dallas Mavericks",       logo:"🤠", color:"#00538C", conf:"West" },
  { abbr:"GSW", name:"Golden State Warriors",  logo:"🌉", color:"#1D428A", conf:"West" },
  { abbr:"LAL", name:"Los Angeles Lakers",     logo:"👑", color:"#552583", conf:"West" },
  { abbr:"PHX", name:"Phoenix Suns",           logo:"☀️", color:"#E56020", conf:"West" },
  { abbr:"SAS", name:"San Antonio Spurs",      logo:"🌹", color:"#8A8D8F", conf:"West" },
  { abbr:"MEM", name:"Memphis Grizzlies",      logo:"🐻", color:"#5D76A9", conf:"West" },
  { abbr:"MIN", name:"Minnesota Timberwolves", logo:"🐺", color:"#0C2340", conf:"West" },
];

// ── Helpers ───────────────────────────────────────────────
function pct(n) { return Math.round(n * 100); }
function hex(c, a=1) {
  const r=parseInt(c.slice(1,3),16), g=parseInt(c.slice(3,5),16), b=parseInt(c.slice(5,7),16);
  return `rgba(${r},${g},${b},${a})`;
}

// ── Main App ──────────────────────────────────────────────
export default function App() {
  const [tab, setTab]         = useState("predict");
  const [home, setHome]       = useState("BOS");
  const [away, setAway]       = useState("LAL");
  const [result, setResult]   = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError]     = useState(null);
  const [teams, setTeams]     = useState([]);
  const [apiStatus, setApiStatus] = useState("checking");

  // API 연결 확인
  useEffect(() => {
    fetch(`${API}/`)
      .then(r => r.ok ? setApiStatus("online") : setApiStatus("offline"))
      .catch(() => setApiStatus("offline"));
  }, []);

  // 팀 목록 로드
  useEffect(() => {
    fetch(`${API}/api/teams`)
      .then(r => r.json())
      .then(setTeams)
      .catch(() => setTeams(TEAMS.map(t => ({ ...t, record: "N/A", net_rating: 0 }))));
  }, []);

  const predict = useCallback(async () => {
    if (home === away) return;
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${API}/api/predictions/predict?home=${home}&away=${away}`);
      if (!r.ok) throw new Error(await r.text());
      setResult(await r.json());
      setTab("result");
    } catch(e) {
      setError("API 연결 실패. 백엔드가 실행 중인지 확인해주세요.");
    } finally {
      setLoading(false);
    }
  }, [home, away]);

  const homeTeam = TEAMS.find(t => t.abbr === home);
  const awayTeam = TEAMS.find(t => t.abbr === away);

  return (
    <div style={styles.root}>
      {/* ── 배경 그라디언트 ── */}
      <div style={styles.bg} />

      {/* ── 헤더 ── */}
      <header style={styles.header}>
        <div style={styles.headerInner}>
          <div style={styles.logo}>
            <span style={styles.logoBall}>🏀</span>
            <div>
              <div style={styles.logoTitle}>NBA PREDICTOR (Prod. Huniboy ㅅㅅㅅ기모띠)</div>
              <div style={styles.logoSub}>ELO · Advanced Stats · Injury · Odds</div>
            </div>
          </div>
          <div style={{
            ...styles.statusBadge,
            background: apiStatus === "online" ? "rgba(0,255,100,0.15)" : "rgba(255,80,80,0.15)",
            borderColor: apiStatus === "online" ? "#00ff64" : "#ff5050",
            color:       apiStatus === "online" ? "#00ff64" : "#ff5050",
          }}>
            <span style={{ fontSize:8, marginRight:5 }}>●</span>
            {apiStatus === "online" ? "LIVE" : apiStatus === "offline" ? "OFFLINE" : "..."}
          </div>
        </div>
      </header>

      {/* ── 탭 ── */}
      <nav style={styles.nav}>
        {[
          { id:"predict", label:"🎯 예측" },
          { id:"result",  label:"📊 결과", disabled: !result },
          { id:"teams",   label:"🏆 팀 순위" },
        ].map(t => (
          <button
            key={t.id}
            disabled={t.disabled}
            onClick={() => setTab(t.id)}
            style={{
              ...styles.tab,
              ...(tab === t.id ? styles.tabActive : {}),
              opacity: t.disabled ? 0.3 : 1,
              cursor:  t.disabled ? "not-allowed" : "pointer",
            }}
          >
            {t.label}
          </button>
        ))}
      </nav>

      {/* ── 컨텐츠 ── */}
      <main style={styles.main}>
        {tab === "predict" && (
          <PredictTab
            home={home} away={away}
            setHome={setHome} setAway={setAway}
            homeTeam={homeTeam} awayTeam={awayTeam}
            onPredict={predict} loading={loading} error={error}
          />
        )}
        {tab === "result" && result && <ResultTab result={result} />}
        {tab === "teams" && <TeamsTab teams={teams} />}
      </main>
    </div>
  );
}

// ── Predict Tab ───────────────────────────────────────────
function PredictTab({ home, away, setHome, setAway, homeTeam, awayTeam, onPredict, loading, error }) {
  return (
    <div style={styles.predictWrap}>
      <div style={styles.matchupCard}>

        {/* VS 레이아웃 */}
        <div style={styles.vsRow}>
          <TeamPicker label="홈 팀" value={home} onChange={setHome} exclude={away} team={homeTeam} />
          <div style={styles.vsCenter}>
            <div style={styles.vsText}>VS</div>
            <div style={styles.vsLine} />
          </div>
          <TeamPicker label="원정 팀" value={away} onChange={setAway} exclude={home} team={awayTeam} />
        </div>

        {/* 예측 버튼 */}
        <button
          onClick={onPredict}
          disabled={loading || home === away}
          style={{ ...styles.predictBtn, opacity: loading ? 0.7 : 1 }}
        >
          {loading ? (
            <span style={styles.spinner}>⏳ 분석 중...</span>
          ) : (
            "⚡ 승률 예측하기"
          )}
        </button>

        {error && <div style={styles.errorBox}>{error}</div>}
      </div>

      {/* 설명 카드 */}
      <div style={styles.infoGrid}>
        {[
          { icon:"📐", title:"ELO 레이팅", desc:"전체 경기 기록 기반 동적 레이팅" },
          { icon:"📈", title:"Advanced Stats", desc:"offRtg · defRtg · pace · TS%" },
          { icon:"🩹", title:"부상 리포트", desc:"NBA 공식 PDF 기반 전력 조정" },
          { icon:"💰", title:"배당 분석", desc:"30+ 북메이커 value bet 탐지" },
        ].map(item => (
          <div key={item.title} style={styles.infoCard}>
            <div style={styles.infoIcon}>{item.icon}</div>
            <div style={styles.infoTitle}>{item.title}</div>
            <div style={styles.infoDesc}>{item.desc}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

function TeamPicker({ label, value, onChange, exclude, team }) {
  return (
    <div style={styles.pickerWrap}>
      <div style={styles.pickerLabel}>{label}</div>
      <div style={{
        ...styles.teamCard,
        borderColor: team ? hex(team.color, 0.6) : "#333",
        boxShadow: team ? `0 0 30px ${hex(team.color, 0.15)}` : "none",
      }}>
        <div style={styles.teamEmoji}>{team?.logo || "🏀"}</div>
        <div style={styles.teamName}>{team?.name || "팀 선택"}</div>
        <select
          value={value}
          onChange={e => onChange(e.target.value)}
          style={styles.select}
        >
          {TEAMS.map(t => (
            <option key={t.abbr} value={t.abbr} disabled={t.abbr === exclude}>
              {t.abbr} — {t.name}
            </option>
          ))}
        </select>
      </div>
    </div>
  );
}

// ── Result Tab ────────────────────────────────────────────
function ResultTab({ result }) {
  const homeProb = pct(result.adj_home_prob);
  const awayProb = pct(result.adj_away_prob);
  const homeTeam = TEAMS.find(t => t.abbr === result.home_abbreviation) || { color: "#007A33", logo: "🏀" };
  const awayTeam = TEAMS.find(t => t.abbr === result.away_abbreviation) || { color: "#552583", logo: "🏀" };
  const isHomeWin = result.adj_home_prob >= 0.5;

  return (
    <div style={styles.resultWrap}>

      {/* 승률 바 */}
      <div style={styles.probCard}>
        <div style={styles.probTeams}>
          <div style={styles.probTeamLeft}>
            <span style={{ fontSize:28 }}>{homeTeam.logo}</span>
            <div>
              <div style={styles.probTeamName}>{result.home_team}</div>
              <div style={styles.probTeamSub}>홈</div>
            </div>
          </div>
          <div style={styles.probScore}>{result.predicted_score}</div>
          <div style={styles.probTeamRight}>
            <div style={{ textAlign:"right" }}>
              <div style={styles.probTeamName}>{result.away_team}</div>
              <div style={styles.probTeamSub}>원정</div>
            </div>
            <span style={{ fontSize:28 }}>{awayTeam.logo}</span>
          </div>
        </div>

        {/* 프로그레스 바 */}
        <div style={styles.probBarWrap}>
          <div style={{
            ...styles.probBarHome,
            width: `${homeProb}%`,
            background: `linear-gradient(90deg, ${homeTeam.color}, ${hex(homeTeam.color, 0.7)})`,
          }}>
            <span style={styles.probBarLabel}>{homeProb}%</span>
          </div>
          <div style={{
            ...styles.probBarAway,
            width: `${awayProb}%`,
            background: `linear-gradient(90deg, ${hex(awayTeam.color, 0.7)}, ${awayTeam.color})`,
          }}>
            <span style={styles.probBarLabel}>{awayProb}%</span>
          </div>
        </div>

        <div style={styles.winnerBadge}>
          <span style={{ color: isHomeWin ? homeTeam.color : awayTeam.color }}>
            {isHomeWin ? homeTeam.logo : awayTeam.logo}
          </span>
          &nbsp;{result.predicted_winner} 승리 예측&nbsp;
          <span style={styles.confBadge(result.confidence)}>
            {result.confidence === "High" ? "🔥 높음" : result.confidence === "Medium" ? "✅ 중간" : "⚠️ 낮음"}
          </span>
        </div>
      </div>

      {/* 팩터 그리드 */}
      <div style={styles.factorGrid}>
        <FactorCard
          title="ELO 레이팅"
          icon="📐"
          home={result.factors.elo.home.toFixed(0)}
          away={result.factors.elo.away.toFixed(0)}
          homeColor={homeTeam.color}
          awayColor={awayTeam.color}
          higherIsBetter
        />
        <FactorCard
          title="Net Rating"
          icon="📈"
          home={result.factors.net_rtg.home > 0 ? `+${result.factors.net_rtg.home}` : result.factors.net_rtg.home}
          away={result.factors.net_rtg.away > 0 ? `+${result.factors.net_rtg.away}` : result.factors.net_rtg.away}
          homeColor={homeTeam.color}
          awayColor={awayTeam.color}
          higherIsBetter
        />
        <FactorCard
          title="최근 5경기"
          icon="🔥"
          home={`${result.factors.form.home}승`}
          away={`${result.factors.form.away}승`}
          homeColor={homeTeam.color}
          awayColor={awayTeam.color}
          higherIsBetter
        />
        <FactorCard
          title="연승/연패"
          icon="⚡"
          home={result.factors.streak.home > 0 ? `${result.factors.streak.home}연승` : `${Math.abs(result.factors.streak.home)}연패`}
          away={result.factors.streak.away > 0 ? `${result.factors.streak.away}연승` : `${Math.abs(result.factors.streak.away)}연패`}
          homeColor={homeTeam.color}
          awayColor={awayTeam.color}
          higherIsBetter
        />
      </div>

      {/* 부상 + 배당 */}
      <div style={styles.extraGrid}>
        <InjuryCard
          label="홈팀 부상"
          impact={result.home_injury_impact}
          players={result.home_injured}
          color={homeTeam.color}
        />
        <InjuryCard
          label="원정팀 부상"
          impact={result.away_injury_impact}
          players={result.away_injured}
          color={awayTeam.color}
        />
        {result.odds ? (
          <OddsCard odds={result.odds} valueBet={result.value_bet} homeColor={homeTeam.color} awayColor={awayTeam.color} />
        ) : (
          <div style={styles.noOddsCard}>
            <div style={{ fontSize:32, marginBottom:8 }}>💰</div>
            <div style={{ color:"#888", fontSize:13 }}>배당 정보 없음</div>
            <div style={{ color:"#555", fontSize:11, marginTop:4 }}>ODDS_API_KEY 설정 시 활성화</div>
          </div>
        )}
      </div>
    </div>
  );
}

function FactorCard({ title, icon, home, away, homeColor, awayColor }) {
  return (
    <div style={styles.factorCard}>
      <div style={styles.factorTitle}>{icon} {title}</div>
      <div style={styles.factorRow}>
        <span style={{ ...styles.factorVal, color: homeColor }}>{home}</span>
        <span style={styles.factorVs}>vs</span>
        <span style={{ ...styles.factorVal, color: awayColor }}>{away}</span>
      </div>
    </div>
  );
}

function InjuryCard({ label, impact, players, color }) {
  const impactPct = Math.round(impact * 100);
  return (
    <div style={styles.injuryCard}>
      <div style={styles.injuryTitle}>🩹 {label}</div>
      <div style={{ ...styles.impactBadge, color, borderColor: hex(color, 0.4) }}>
        전력 손실 {impactPct}%
      </div>
      {players.length === 0 ? (
        <div style={styles.noInjury}>부상 선수 없음 ✅</div>
      ) : (
        players.map(p => (
          <div key={p.player_name} style={styles.injuryRow}>
            <div style={styles.injuryName}>{p.player_name}</div>
            <div style={styles.injuryStatus(p.status)}>{p.status}</div>
          </div>
        ))
      )}
    </div>
  );
}

function OddsCard({ odds, valueBet, homeColor, awayColor }) {
  return (
    <div style={styles.oddsCard}>
      <div style={styles.oddsTitle}>💰 배당 분석</div>
      <div style={styles.oddsRow}>
        <div style={styles.oddsItem}>
          <div style={styles.oddsLabel}>홈</div>
          <div style={{ ...styles.oddsValue, color: homeColor }}>{odds.home_ml_american}</div>
          <div style={styles.oddsImplied}>{pct(odds.implied_home_prob)}%</div>
        </div>
        <div style={styles.oddsDivider} />
        <div style={styles.oddsItem}>
          <div style={styles.oddsLabel}>원정</div>
          <div style={{ ...styles.oddsValue, color: awayColor }}>{odds.away_ml_american}</div>
          <div style={styles.oddsImplied}>{pct(odds.implied_away_prob)}%</div>
        </div>
        <div style={styles.oddsDivider} />
        <div style={styles.oddsItem}>
          <div style={styles.oddsLabel}>스프레드</div>
          <div style={styles.oddsValue}>{odds.home_spread}</div>
          <div style={styles.oddsLabel}>총점 {odds.total_line}</div>
        </div>
      </div>
      {valueBet?.has_value && (
        <div style={styles.valueBetBanner}>
          <div>{valueBet.strength}</div>
          <div style={{ fontSize:11, marginTop:2, color:"#aaa" }}>
            {valueBet.best_bet === "home" ? "홈팀" : "원정팀"} 엣지 {Math.round((valueBet.best_bet === "home" ? valueBet.home_edge : valueBet.away_edge) * 100)}%
            · Kelly {Math.round((valueBet.best_bet === "home" ? valueBet.home_kelly_frac : valueBet.away_kelly_frac) * 100)}%
          </div>
        </div>
      )}
      <div style={styles.vigRow}>Vig {odds.vig_pct?.toFixed(1)}% · {odds.bookmaker_count}개 북메이커</div>
    </div>
  );
}

// ── Teams Tab ─────────────────────────────────────────────
function TeamsTab({ teams }) {
  const east = teams.filter(t => t.conference === "East").sort((a,b) => b.net_rating - a.net_rating);
  const west = teams.filter(t => t.conference === "West").sort((a,b) => b.net_rating - a.net_rating);

  return (
    <div style={styles.teamsWrap}>
      {[{ label:"🌍 East", teams: east }, { label:"🌎 West", teams: west }].map(conf => (
        <div key={conf.label} style={styles.confBlock}>
          <div style={styles.confTitle}>{conf.label}</div>
          {conf.teams.map((t, i) => {
            const team = TEAMS.find(x => x.abbr === t.abbreviation) || {};
            return (
              <div key={t.abbreviation} style={styles.teamRow(team.color)}>
                <div style={styles.teamRank}>{i + 1}</div>
                <div style={styles.teamLogo}>{team.logo}</div>
                <div style={styles.teamInfo}>
                  <div style={styles.teamRowName}>{t.name}</div>
                  <div style={styles.teamRowRecord}>{t.record}</div>
                </div>
                <div style={{
                  ...styles.netRatingBadge,
                  color: t.net_rating > 0 ? "#00ff88" : "#ff6b6b",
                }}>
                  {t.net_rating > 0 ? "+" : ""}{t.net_rating?.toFixed(1)}
                </div>
              </div>
            );
          })}
        </div>
      ))}
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────
const styles = {
  root: {
    minHeight: "100vh",
    background: "#0a0a0f",
    color: "#fff",
    fontFamily: "'Barlow Condensed', 'Impact', system-ui, sans-serif",
    position: "relative",
    overflowX: "hidden",
  },
  bg: {
    position: "fixed", inset: 0, zIndex: 0,
    background: "radial-gradient(ellipse at 20% 20%, rgba(0,122,51,0.08) 0%, transparent 50%), radial-gradient(ellipse at 80% 80%, rgba(85,37,131,0.08) 0%, transparent 50%)",
    pointerEvents: "none",
  },
  header: {
    position: "relative", zIndex: 10,
    borderBottom: "1px solid rgba(255,255,255,0.08)",
    background: "rgba(10,10,15,0.9)",
    backdropFilter: "blur(20px)",
  },
  headerInner: {
    maxWidth: 900, margin: "0 auto", padding: "16px 20px",
    display: "flex", alignItems: "center", justifyContent: "space-between",
  },
  logo: { display: "flex", alignItems: "center", gap: 12 },
  logoBall: { fontSize: 32 },
  logoTitle: { fontSize: 22, fontWeight: 900, letterSpacing: 3, color: "#fff" },
  logoSub: { fontSize: 10, color: "#555", letterSpacing: 2, marginTop: 2 },
  statusBadge: {
    padding: "4px 12px", borderRadius: 20, border: "1px solid",
    fontSize: 11, fontWeight: 700, letterSpacing: 2,
  },
  nav: {
    position: "relative", zIndex: 10,
    display: "flex", maxWidth: 900, margin: "0 auto", padding: "0 20px",
    gap: 4, borderBottom: "1px solid rgba(255,255,255,0.06)",
  },
  tab: {
    padding: "12px 20px", background: "none", border: "none",
    color: "#555", fontSize: 13, fontWeight: 700, letterSpacing: 1,
    transition: "all 0.2s", borderBottom: "2px solid transparent",
  },
  tabActive: {
    color: "#fff", borderBottom: "2px solid #e8a020",
  },
  main: {
    position: "relative", zIndex: 10,
    maxWidth: 900, margin: "0 auto", padding: "24px 20px",
  },
  predictWrap: { display: "flex", flexDirection: "column", gap: 24 },
  matchupCard: {
    background: "rgba(255,255,255,0.03)",
    border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 16, padding: 28,
  },
  vsRow: { display: "flex", alignItems: "center", gap: 16, marginBottom: 24 },
  vsCenter: { display: "flex", flexDirection: "column", alignItems: "center", gap: 8 },
  vsText: { fontSize: 28, fontWeight: 900, color: "#e8a020", letterSpacing: 4 },
  vsLine: { width: 2, height: 60, background: "rgba(232,160,32,0.2)" },
  pickerWrap: { flex: 1, display: "flex", flexDirection: "column", gap: 8 },
  pickerLabel: { fontSize: 11, color: "#555", letterSpacing: 2, fontWeight: 700 },
  teamCard: {
    position: "relative", padding: "20px 16px",
    background: "rgba(255,255,255,0.04)",
    border: "1px solid", borderRadius: 12,
    display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
    transition: "all 0.3s",
  },
  teamEmoji: { fontSize: 36 },
  teamName: { fontSize: 13, fontWeight: 700, textAlign: "center", color: "#ccc" },
  select: {
    position: "absolute", inset: 0, opacity: 0, cursor: "pointer", width: "100%", fontSize: 16,
  },
  predictBtn: {
    width: "100%", padding: "16px 0",
    background: "linear-gradient(135deg, #e8a020, #f4c842)",
    border: "none", borderRadius: 12, cursor: "pointer",
    fontSize: 16, fontWeight: 900, color: "#000", letterSpacing: 2,
    transition: "all 0.2s",
  },
  spinner: { display: "inline-block" },
  errorBox: {
    marginTop: 12, padding: "12px 16px",
    background: "rgba(255,80,80,0.1)", border: "1px solid rgba(255,80,80,0.3)",
    borderRadius: 8, color: "#ff6b6b", fontSize: 13,
  },
  infoGrid: { display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 12 },
  infoCard: {
    padding: "16px 12px", textAlign: "center",
    background: "rgba(255,255,255,0.03)",
    border: "1px solid rgba(255,255,255,0.06)", borderRadius: 10,
  },
  infoIcon: { fontSize: 24, marginBottom: 6 },
  infoTitle: { fontSize: 11, fontWeight: 700, color: "#e8a020", letterSpacing: 1, marginBottom: 4 },
  infoDesc: { fontSize: 11, color: "#555", lineHeight: 1.4 },
  resultWrap: { display: "flex", flexDirection: "column", gap: 16 },
  probCard: {
    background: "rgba(255,255,255,0.04)", border: "1px solid rgba(255,255,255,0.08)",
    borderRadius: 16, padding: 24,
  },
  probTeams: { display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 20 },
  probTeamLeft:  { display: "flex", alignItems: "center", gap: 12 },
  probTeamRight: { display: "flex", alignItems: "center", gap: 12 },
  probTeamName: { fontSize: 15, fontWeight: 700 },
  probTeamSub: { fontSize: 11, color: "#555", marginTop: 2 },
  probScore: { fontSize: 28, fontWeight: 900, color: "#e8a020" },
  probBarWrap: { display: "flex", height: 36, borderRadius: 8, overflow: "hidden", marginBottom: 16 },
  probBarHome: {
    display: "flex", alignItems: "center", justifyContent: "center",
    transition: "width 0.8s ease",
  },
  probBarAway: {
    display: "flex", alignItems: "center", justifyContent: "center",
    transition: "width 0.8s ease",
  },
  probBarLabel: { fontSize: 13, fontWeight: 900, color: "#fff" },
  winnerBadge: {
    display: "flex", alignItems: "center", justifyContent: "center",
    gap: 6, fontSize: 14, fontWeight: 700, color: "#ccc",
  },
  confBadge: (c) => ({
    padding: "2px 10px", borderRadius: 20, fontSize: 11, fontWeight: 700,
    background: c === "High" ? "rgba(255,80,80,0.2)" : c === "Medium" ? "rgba(232,160,32,0.2)" : "rgba(100,100,100,0.2)",
    color: c === "High" ? "#ff6b6b" : c === "Medium" ? "#e8a020" : "#888",
  }),
  factorGrid: { display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 },
  factorCard: {
    padding: "14px 12px",
    background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 10,
  },
  factorTitle: { fontSize: 10, color: "#555", letterSpacing: 1, marginBottom: 8 },
  factorRow: { display: "flex", alignItems: "center", justifyContent: "space-between" },
  factorVal: { fontSize: 16, fontWeight: 900 },
  factorVs: { fontSize: 10, color: "#444" },
  extraGrid: { display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 },
  injuryCard: {
    padding: 16,
    background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 12,
  },
  injuryTitle: { fontSize: 12, fontWeight: 700, color: "#ccc", marginBottom: 10 },
  impactBadge: {
    display: "inline-block", padding: "3px 10px",
    border: "1px solid", borderRadius: 20, fontSize: 11, marginBottom: 10,
  },
  noInjury: { fontSize: 12, color: "#555" },
  injuryRow: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 6 },
  injuryName: { fontSize: 12, color: "#ccc" },
  injuryStatus: (s) => ({
    fontSize: 10, fontWeight: 700, padding: "2px 8px", borderRadius: 10,
    background: s === "Out" ? "rgba(255,80,80,0.2)" : s === "Doubtful" ? "rgba(255,140,0,0.2)" : "rgba(255,220,0,0.2)",
    color: s === "Out" ? "#ff6b6b" : s === "Doubtful" ? "#ff8c00" : "#ffd700",
  }),
  oddsCard: {
    padding: 16,
    background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.07)",
    borderRadius: 12,
  },
  oddsTitle: { fontSize: 12, fontWeight: 700, color: "#ccc", marginBottom: 12 },
  oddsRow: { display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 12 },
  oddsItem: { flex: 1, textAlign: "center" },
  oddsLabel: { fontSize: 10, color: "#555", marginBottom: 4 },
  oddsValue: { fontSize: 18, fontWeight: 900, marginBottom: 2 },
  oddsImplied: { fontSize: 10, color: "#666" },
  oddsDivider: { width: 1, height: 40, background: "rgba(255,255,255,0.08)" },
  valueBetBanner: {
    padding: "10px 14px", borderRadius: 8, marginBottom: 8,
    background: "rgba(232,160,32,0.1)", border: "1px solid rgba(232,160,32,0.3)",
    fontSize: 13, fontWeight: 700, color: "#e8a020",
  },
  vigRow: { fontSize: 10, color: "#444", textAlign: "center" },
  noOddsCard: {
    padding: 20, textAlign: "center",
    background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.05)",
    borderRadius: 12, display: "flex", flexDirection: "column", alignItems: "center", justifyContent: "center",
  },
  teamsWrap: { display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 },
  confBlock: {},
  confTitle: {
    fontSize: 16, fontWeight: 900, color: "#e8a020",
    letterSpacing: 2, marginBottom: 12,
  },
  teamRow: (color) => ({
    display: "flex", alignItems: "center", gap: 12, padding: "10px 14px",
    background: "rgba(255,255,255,0.03)", borderRadius: 8, marginBottom: 6,
    borderLeft: `3px solid ${color || "#333"}`,
    transition: "background 0.2s",
  }),
  teamRank: { fontSize: 12, color: "#444", width: 16, textAlign: "center", fontWeight: 700 },
  teamLogo: { fontSize: 20 },
  teamInfo: { flex: 1 },
  teamRowName: { fontSize: 13, fontWeight: 700 },
  teamRowRecord: { fontSize: 11, color: "#555", marginTop: 2 },
  netRatingBadge: { fontSize: 13, fontWeight: 900 },
};
