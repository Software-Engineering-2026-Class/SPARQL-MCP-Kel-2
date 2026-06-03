# SPARQL test suite — security queries

Dokumen ini berisi kueri uji keamanan SPARQL, metrik penilaian, dan prosedur evaluasi. Kueri dirancang untuk menguji kemampuan sistem dalam mengekstraksi informasi keamanan dari SEPSES CSKG, termasuk CVE, CWE, CAPEC, dan Snort rules. Setiap kueri mencakup template SPARQL, variannya, expected bindings, dan catatan pemetaan ke struktur data CSKG.

## Ringkasan
- Jumlah kueri: 15 (variasi untuk CAPEC & Snort ditambahkan)
- Output: template SPARQL, variannya, expected bindings, catatan pemetaan ke SEPSES CSKG

## Asumsi
- Terdapat endpoint SPARQL untuk SEPSES CSKG.
- Prefix umum dipakai: `cskg:`, `rdf:`, `rdfs:`, `xsd:`. Ganti IRI sesuai skema lokal bila perlu.

## Prefix (contoh)
```sparql
PREFIX cskg: <http://example.org/cskg/>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
```

---

## Kueri uji (15) — NL, SPARQL template, expected vars, notes

1) NL: Which CVE identifiers exist for vulnerabilities affecting OpenSSL?

SPARQL:
```sparql
SELECT ?cve WHERE {
  ?v rdf:type cskg:Vulnerability .
  ?v cskg:affectsProduct ?prod .
  ?prod rdfs:label "OpenSSL" .
  ?v cskg:cveId ?cve .
}
```
Expected: `?cve`

2) NL: Affected versions for Apache HTTP Server CVE `CVE-2021-41773`.

SPARQL:
```sparql
SELECT ?version WHERE {
  ?v cskg:cveId "CVE-2021-41773" .
  ?v cskg:affectsVersion ?version .
}
```
Expected: `?version`

3) NL: CVSS v3 base scores and severity for vulnerabilities in nginx.

SPARQL:
```sparql
SELECT ?cve ?score ?severity WHERE {
  ?v rdf:type cskg:Vulnerability .
  ?v cskg:affectsProduct ?p .
  ?p rdfs:label "nginx" .
  ?v cskg:cveId ?cve .
  ?v cskg:cvssV3BaseScore ?score .
  ?v cskg:cvssV3Severity ?severity .
}
```
Expected: `?cve`, `?score`, `?severity`

4) NL: Vulnerabilities with public PoC targeting Windows Server.

SPARQL:
```sparql
SELECT ?cve ?poc WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:affectsProduct ?prod .
  ?prod rdfs:label "Windows Server" .
  ?v cskg:exploitProofOfConcept ?poc .
}
```
Expected: `?cve`, `?poc`

5) NL: Map CVE `CVE-2017-0144` to CWEs and MITRE ATT&CK techniques.

SPARQL:
```sparql
SELECT ?cwe ?tech WHERE {
  ?v cskg:cveId "CVE-2017-0144" .
  OPTIONAL { ?v cskg:hasCWE ?cwe . }
  OPTIONAL { ?v cskg:relatedTechnique ?tech . }
}
```
Expected: `?cwe`, `?tech`

6) NL: Vendors reporting CRITICAL vulnerabilities in last 12 months.

SPARQL (ganti tanggal):
```sparql
SELECT DISTINCT ?vendor ?cve WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:reportedBy ?vendor .
  ?v cskg:cvssV3Severity "CRITICAL" .
  ?v cskg:publishDate ?date .
  FILTER(?date > xsd:date("2025-06-01"))
}
```
Expected: `?vendor`, `?cve`

7) NL: For PostgreSQL, remediation/patch URL and release date per CVE.

SPARQL:
```sparql
SELECT ?cve ?patchUrl ?patchDate WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:affectsProduct ?p .
  ?p rdfs:label "PostgreSQL" .
  OPTIONAL { ?v cskg:patchURL ?patchUrl . }
  OPTIONAL { ?v cskg:patchDate ?patchDate . }
}
```
Expected: `?cve`, `?patchUrl`, `?patchDate`

8) NL: Top 10 most frequent CWEs across all CVEs.

SPARQL:
```sparql
SELECT ?cwe (COUNT(?v) AS ?count) WHERE {
  ?v cskg:hasCWE ?cwe .
} GROUP BY ?cwe ORDER BY DESC(?count) LIMIT 10
```
Expected: `?cwe`, `?count`

9) NL: CVEs referencing GitHub PoC and commit date.

SPARQL:
```sparql
SELECT ?cve ?poc ?commitDate WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:exploitProofOfConcept ?poc .
  FILTER(STRSTARTS(STR(?poc),"https://github.com/"))
  OPTIONAL { ?v cskg:pocCommitDate ?commitDate . }
}
```
Expected: `?cve`, `?poc`, `?commitDate`

10) NL: Vulnerabilities enabling RCE and affected OS families.

SPARQL:
```sparql
SELECT ?cve ?impact ?osFamily WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:impact ?impact .
  FILTER(CONTAINS(LCASE(STR(?impact)),"remote code execution") || CONTAINS(LCASE(STR(?impact)),"rce")) .
  ?v cskg:affectsProduct ?prod .
  ?prod cskg:osFamily ?osFamily .
}
```
Expected: `?cve`, `?impact`, `?osFamily`

11) NL: Monthly count of new CVEs in 2024 for vendor Cisco.

SPARQL:
```sparql
SELECT (MONTH(?date) AS ?month) (COUNT(?v) AS ?count) WHERE {
  ?v cskg:reportedBy ?vendor .
  ?vendor rdfs:label "Cisco" .
  ?v cskg:publishDate ?date .
  FILTER(YEAR(?date) = 2024)
} GROUP BY ?month ORDER BY ?month
```
Expected: `?month`, `?count`

12) NL: Authoritative references for CVE `CVE-2020-0796`.

SPARQL:
```sparql
SELECT ?source ?url WHERE {
  ?v cskg:cveId "CVE-2020-0796" .
  ?v cskg:reference ?ref .
  ?ref cskg:source ?source .
  ?ref cskg:url ?url .
}
```
Expected: `?source`, `?url`

--- Variasi CAPEC & Snort rule (ditambahkan)

13) NL: Map CVE to CAPEC IDs and CAPEC names.

SPARQL:
```sparql
SELECT ?cve ?capecId ?capecName WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:relatedCAPEC ?capec .
  ?capec cskg:capecId ?capecId .
  ?capec rdfs:label ?capecName .
}
```
Expected: `?cve`, `?capecId`, `?capecName`

14) NL: CAPEC techniques most associated with RCE CVEs.

SPARQL:
```sparql
SELECT ?capec (COUNT(?v) AS ?count) WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:relatedCAPEC ?capec .
  ?v cskg:impact ?impact .
  FILTER(CONTAINS(LCASE(STR(?impact)),"remote code execution") || CONTAINS(LCASE(STR(?impact)),"rce"))
} GROUP BY ?capec ORDER BY DESC(?count) LIMIT 10
```
Expected: `?capec`, `?count`

15) NL: Find Snort rule IDs or signatures that reference a CVE and the rule text.

SPARQL:
```sparql
SELECT ?cve ?snortId ?ruleText WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:hasSnortRule ?rule .
  ?rule cskg:snortId ?snortId .
  ?rule cskg:ruleText ?ruleText .
}
```
Expected: `?cve`, `?snortId`, `?ruleText`

16) NL (bonus): CVEs that have active Snort rules (domain of rule source) and PoC present.

SPARQL:
```sparql
SELECT ?cve ?snortId ?poc WHERE {
  ?v cskg:cveId ?cve .
  ?v cskg:hasSnortRule ?rule .
  ?rule cskg:snortId ?snortId .
  ?v cskg:exploitProofOfConcept ?poc .
}
```
Expected: `?cve`, `?snortId`, `?poc`

---
