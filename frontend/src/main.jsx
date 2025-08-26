import React, {useState} from "react"
import { createRoot } from "react-dom/client"

const API = import.meta.env.VITE_API_BASE

async function searchFlights(payload){
  const r = await fetch(`${API}/api/search`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if(!r.ok) throw new Error(await r.text())
  return (await r.json()).results || []
}

function App(){
  const [origins, setOrigins] = useState("LHR,MAN")
  const [dests, setDests] = useState("DEL,HYD")
  const [date, setDate] = useState("2025-10-10")
  const [rows, setRows] = useState([])
  const [loading, setLoading] = useState(false)
  const [err, setErr] = useState("")

  async function onSearch(){
    setLoading(true); setErr("")
    try{
      const results = await searchFlights({
        origins: origins.split(",").map(s=>s.trim()).filter(Boolean),
        destinations: dests.split(",").map(s=>s.trim()).filter(Boolean),
        depart_date: date, return_date: null, adults: 1, days_flex: 1, limit_per_route: 20
      })
      setRows(results)
    }catch(e){ setErr(String(e)) }
    finally{ setLoading(false) }
  }

  return (
    <div style={{padding:20, fontFamily:"system-ui"}}>
      <h2>Cheapest Flight Agent (Mock)</h2>
      <div style={{display:"grid", gridTemplateColumns:"1fr 1fr 1fr", gap:10}}>
        <div>
          <div>Origins (comma separated)</div>
          <input value={origins} onChange={e=>setOrigins(e.target.value)} />
        </div>
        <div>
          <div>Destinations (comma separated)</div>
          <input value={dests} onChange={e=>setDests(e.target.value)} />
        </div>
        <div>
          <div>Depart date</div>
          <input type="date" value={date} onChange={e=>setDate(e.target.value)} />
        </div>
      </div>
      <div style={{marginTop:10}}>
        <button onClick={onSearch} disabled={loading}>{loading? "Searching…":"Search"}</button>
      </div>
      {err && <div style={{color:"crimson", marginTop:8}}>{err}</div>}
      <table style={{marginTop:16, width:"100%", borderCollapse:"collapse"}}>
        <thead><tr><th>Route</th><th>Date</th><th>Stops</th><th>Duration</th><th>Price</th><th>Provider</th></tr></thead>
        <tbody>
          {rows.map((r,i)=>(
            <tr key={i} style={{borderTop:"1px solid #ddd"}}>
              <td>{r.origin} → {r.destination}</td>
              <td>{r.out_date}</td>
              <td style={{textAlign:"center"}}>{r.stops}</td>
              <td style={{textAlign:"center"}}>{Math.floor(r.duration_minutes/60)}h</td>
              <td style={{textAlign:"center"}}>{r.price} {r.currency}</td>
              <td style={{textAlign:"center"}}>{r.provider}</td>
            </tr>
          ))}
          {!rows.length && <tr><td colSpan="6" style={{padding:8, opacity:.7}}>No results yet.</td></tr>}
        </tbody>
      </table>
    </div>
  )
}

createRoot(document.getElementById("root")).render(<App />)
