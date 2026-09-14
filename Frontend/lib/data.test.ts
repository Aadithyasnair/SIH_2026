import { describe, expect, it } from "vitest";
import { demoAlerts, demoClusters, getRisk } from "./data";
describe("frontend data adapters",()=>{it("maps risk thresholds to accessible labels",()=>{expect(getRisk(.71).label).toBe("High risk");expect(getRisk(.4).label).toBe("Medium risk");expect(getRisk(.39).label).toBe("Low risk")});it("keeps drill-down and cluster records complete",()=>{expect(demoAlerts.every(a=>a.explanation&&a.txid&&a.flags.length)).toBe(true);expect(demoClusters.every(c=>c.member_count===c.member_addresses.length)).toBe(true)})});
