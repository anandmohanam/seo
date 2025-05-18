import streamlit as st
import requests
from bs4 import BeautifulSoup
from collections import Counter
from fpdf import FPDF
import tldextract
import re
import os
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()
API_KEY = os.getenv("PAGESPEED_API_KEY")

# Set page config (try-except to avoid errors)
try:
    st.set_page_config(page_title="SEO Structure Analyzer", layout="wide", page_icon="🔍")
except Exception:
    pass

# Custom CSS for input box size
st.markdown("""
    <style>
    .small-input input {
        font-size: 14px !important;
        padding: 4px !important;
        height: 32px !important;
        width: 300px !important;
    }
    </style>
""", unsafe_allow_html=True)


def fetch_html(url):
    return requests.get(url, headers={"User-Agent": "Mozilla/5.0"})


def get_pagespeed_scores(url):
    scores = {}
    endpoint = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
    for strategy in ["desktop", "mobile"]:
        try:
            params = {"url": url, "key": API_KEY, "strategy": strategy}
            response = requests.get(endpoint, params=params, timeout=20)
            data = response.json()
            categories = data["lighthouseResult"]["categories"]
            scores[strategy.capitalize()] = {
                "Performance": round(categories["performance"]["score"] * 100),
                "Accessibility": round(categories["accessibility"]["score"] * 100),
                "Best Practices": round(categories["best-practices"]["score"] * 100),
                "SEO": round(categories["seo"]["score"] * 100),
            }
        except requests.exceptions.ReadTimeout:
            scores[strategy.capitalize()] = "Error: PageSpeed API request timed out"
        except Exception as e:
            scores[strategy.capitalize()] = f"Error: {e}"
    return scores


def keyword_analysis(text):
    text = re.sub(r"[^\w\s]", "", text.lower())
    words = text.split()
    return Counter(words).most_common(10)


def generate_pdf_report(data):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", size=12)
    for section, content in data.items():
        pdf.set_font("Helvetica", "B", 14)
        pdf.cell(0, 10, text=section, ln=True)
        pdf.set_font("Helvetica", size=12)
        if isinstance(content, dict):
            for k, v in content.items():
                if isinstance(v, list):
                    pdf.multi_cell(0, 8, text=f"{k}:")
                    for item in v:
                        pdf.multi_cell(0, 8, text=f"  - {item}")
                else:
                    pdf.multi_cell(0, 8, text=f"{k}: {v}")
        elif isinstance(content, list):
            for item in content:
                pdf.multi_cell(0, 8, text=f"- {item}")
        else:
            pdf.multi_cell(0, 8, text=str(content))
        pdf.ln()
    return pdf.output(dest='S').encode('latin-1')


def detect_technology(url, soup, response_headers):
    tech = set()
    # Check headers
    x_powered_by = response_headers.get("X-Powered-By", "")
    server = response_headers.get("Server", "")
    if x_powered_by:
        tech.add(f"X-Powered-By: {x_powered_by}")
    if server:
        tech.add(f"Server: {server}")

    # Meta generator tag
    meta_gen = soup.find("meta", attrs={"name": "generator"})
    if meta_gen and meta_gen.get("content"):
        tech.add(f"Generator: {meta_gen['content']}")

    html_str = str(soup).lower()

    # CMS and platforms
    if "wp-content" in html_str or "wordpress" in html_str:
        tech.add("WordPress")
    if "shopify" in html_str:
        tech.add("Shopify")
    if "drupal" in html_str:
        tech.add("Drupal")
    if "joomla" in html_str:
        tech.add("Joomla")
    if "magento" in html_str:
        tech.add("Magento")
    if "wix.com" in html_str:
        tech.add("Wix")
    if "squarespace" in html_str:
        tech.add("Squarespace")

    # JavaScript frameworks
    if re.search(r"\breact\b", html_str):
        tech.add("React.js")
    if re.search(r"\bangular\b", html_str):
        tech.add("Angular")
    if re.search(r"\bvue\b", html_str):
        tech.add("Vue.js")
    if re.search(r"next.js", html_str):
        tech.add("Next.js")
    if re.search(r"nuxt.js", html_str):
        tech.add("Nuxt.js")
    if re.search(r"ember.js", html_str):
        tech.add("Ember.js")

    # Backend frameworks (heuristic)
    if "django" in html_str:
        tech.add("Django")
    if "flask" in html_str:
        tech.add("Flask")
    if "laravel" in html_str:
        tech.add("Laravel")
    if "ruby on rails" in html_str or "rails" in html_str:
        tech.add("Ruby on Rails")
    if "express" in html_str:
        tech.add("Express.js")
    if "php" in html_str:
        tech.add("PHP")

    # Web servers
    if "apache" in server.lower():
        tech.add("Apache HTTP Server")
    if "nginx" in server.lower():
        tech.add("Nginx")

    if not tech:
        tech.add("Technology not detected")

    return ", ".join(sorted(tech))


# --- Main App ---

st.markdown("<h1 style='text-align:center; margin-bottom: 20px;'>SEO Structure Analyzer</h1>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    st.markdown('<div class="small-input">', unsafe_allow_html=True)
    url = st.text_input("Enter full URL (including https://)", placeholder="https://example.com", key="url_input")
    st.markdown('</div>', unsafe_allow_html=True)
    analyze_btn = st.button("Start Analysis")

if analyze_btn:
    if not url.strip():
        st.warning("Please enter a valid URL.")
    else:
        with st.spinner("Analyzing SEO structure... please wait"):
            start_time = time.time()
            try:
                response = fetch_html(url)
                response.raise_for_status()
                html = response.content
                soup = BeautifulSoup(html, "lxml")
                seo_report = {}

                # Meta Information
                st.markdown("### Meta Information")
                title = soup.title.string if soup.title else "N/A"
                meta_desc = soup.find("meta", attrs={"name": "description"})
                meta_desc = meta_desc["content"] if meta_desc else "N/A"
                canonical = soup.find("link", rel="canonical")
                canonical_url = canonical["href"] if canonical else "N/A"
                st.write("**Title:**", title)
                st.write("**Meta Description:**", meta_desc)
                st.write("**Canonical URL:**", canonical_url)
                seo_report["Meta Information"] = {
                    "Title": title,
                    "Meta Description": meta_desc,
                    "Canonical URL": canonical_url
                }

                # Headings
                st.markdown("---")
                st.markdown("### Headings")
                headings = {}
                for i in range(1, 7):
                    tags = soup.find_all(f"h{i}")
                    tag_texts = [tag.get_text(strip=True) for tag in tags]
                    headings[f"H{i}"] = tag_texts

                cols = st.columns(3)
                for i, (level, texts) in enumerate(headings.items()):
                    with cols[i % 3]:
                        with st.expander(f"{level} ({len(texts)})"):
                            for t in texts:
                                st.markdown(f"- {t}")
                seo_report["Headings"] = headings

                # Images & Links
                st.markdown("---")
                st.markdown("### Images & Links")
                images = soup.find_all("img")
                alt_missing = len([img for img in images if not img.get("alt")])
                all_links = soup.find_all("a", href=True)
                ext = tldextract.extract(url).domain
                internal_links = [a for a in all_links if ext in a["href"]]
                external_links = [a for a in all_links if ext not in a["href"]]
                st.write("Total images:", len(images))
                st.write("Images missing alt attributes:", alt_missing)
                st.write("Internal Links:", len(internal_links))
                st.write("External Links:", len(external_links))
                seo_report["Images"] = {"Total Images": len(images), "Missing Alt Attributes": alt_missing}
                seo_report["Links"] = {"Total": len(all_links), "Internal": len(internal_links), "External": len(external_links)}

                # Keyword Frequency
                st.markdown("---")
                st.markdown("### Keyword Frequency")
                body_text = soup.get_text(separator=' ')
                keywords = keyword_analysis(body_text)
                for word, freq in keywords:
                    st.write(f"{word}: {freq}")
                seo_report["Top Keywords"] = {word: freq for word, freq in keywords}

                # Structured Data
                st.markdown("---")
                st.markdown("### Structured Data (Schema Markup)")
                schema_data = soup.find_all("script", type="application/ld+json")
                if schema_data:
                    st.success(f"Found {len(schema_data)} JSON-LD scripts.")
                    for i, script in enumerate(schema_data, 1):
                        st.code(script.string.strip(), language='json')
                    seo_report["Schema Markup"] = f"{len(schema_data)} JSON-LD scripts found"
                else:
                    st.warning("No JSON-LD structured data found.")
                    seo_report["Schema Markup"] = "Not Found"

                # robots.txt and sitemap.xml
                st.markdown("---")
                st.markdown("### robots.txt and sitemap.xml")
                parsed = tldextract.extract(url)
                domain = f"https://{parsed.domain}.{parsed.suffix}"
                robots_url = domain + "/robots.txt"
                sitemap_url = domain + "/sitemap.xml"

                try:
                    robots_resp = requests.get(robots_url, timeout=10)
                    sitemap_resp = requests.get(sitemap_url, timeout=10)
                    st.write("robots.txt status:", robots_resp.status_code)
                    st.write("sitemap.xml status:", sitemap_resp.status_code)
                    st.code(robots_resp.text[:500] + ("..." if len(robots_resp.text) > 500 else ""), language='plaintext')
                    st.code(sitemap_resp.text[:500] + ("..." if len(sitemap_resp.text) > 500 else ""), language='xml')
                    seo_report["robots.txt"] = robots_resp.text[:1000]
                    seo_report["sitemap.xml"] = sitemap_resp.text[:1000]
                except Exception as e:
                    st.error(f"Error fetching robots.txt or sitemap.xml: {e}")

                # Google PageSpeed Insights
                st.markdown("---")
                st.markdown("### Google PageSpeed Insights Scores")
                if API_KEY:
                    scores = get_pagespeed_scores(url)
                    for device, score_dict in scores.items():
                        st.markdown(f"**{device}**")
                        if isinstance(score_dict, dict):
                            for k, v in score_dict.items():
                                st.write(f"{k}: {v}")
                        else:
                            st.write(score_dict)
                    seo_report["PageSpeed Insights"] = scores
                else:
                    st.warning("PageSpeed API key not provided. Skipping this section.")

                # Detect Technologies
                st.markdown("---")
                st.markdown("### Detected Technologies / Platforms / Servers")
                detected_technology = detect_technology(url, soup, response.headers)
                st.info(detected_technology)
                seo_report["Detected Technologies"] = detected_technology

                # PDF download
                pdf_data = generate_pdf_report(seo_report)
                st.download_button("Download SEO Report as PDF", data=pdf_data, file_name="seo_report.pdf", mime="application/pdf")

            except Exception as e:
                st.error(f"Error analyzing the URL: {e}")
            finally:
                st.info(f"Analysis completed in {time.time() - start_time:.2f} seconds.")
