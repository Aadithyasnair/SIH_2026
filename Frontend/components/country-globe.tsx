"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { Alert, getRisk, isDarknetOrTor } from "@/lib/data";
import { NetworkEvent } from "@/lib/api";

export const countryCoordinates: Record<string, { lat: number; lng: number; name: string }> = {
  // Standard & Initial Set (Kept Authoritative)
  US: { lat: 37.09, lng: -95.71, name: "United States" },
  USA: { lat: 37.09, lng: -95.71, name: "United States" },
  "United States": { lat: 37.09, lng: -95.71, name: "United States" },
  "United States of America": { lat: 37.09, lng: -95.71, name: "United States" },
  DE: { lat: 51.16, lng: 10.45, name: "Germany" },
  DEU: { lat: 51.16, lng: 10.45, name: "Germany" },
  Germany: { lat: 51.16, lng: 10.45, name: "Germany" },
  NL: { lat: 52.13, lng: 5.29, name: "Netherlands" },
  NLD: { lat: 52.13, lng: 5.29, name: "Netherlands" },
  Netherlands: { lat: 52.13, lng: 5.29, name: "Netherlands" },
  "The Netherlands": { lat: 52.13, lng: 5.29, name: "Netherlands" },
  Holland: { lat: 52.13, lng: 5.29, name: "Netherlands" },
  SE: { lat: 60.12, lng: 18.64, name: "Sweden" },
  SWE: { lat: 60.12, lng: 18.64, name: "Sweden" },
  Sweden: { lat: 60.12, lng: 18.64, name: "Sweden" },
  CH: { lat: 46.81, lng: 8.22, name: "Switzerland" },
  CHE: { lat: 46.81, lng: 8.22, name: "Switzerland" },
  Switzerland: { lat: 46.81, lng: 8.22, name: "Switzerland" },
  JP: { lat: 36.20, lng: 138.25, name: "Japan" },
  JPN: { lat: 36.20, lng: 138.25, name: "Japan" },
  Japan: { lat: 36.20, lng: 138.25, name: "Japan" },
  GB: { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  GBR: { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  UK: { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  "United Kingdom": { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  "Great Britain": { lat: 55.37, lng: -3.43, name: "United Kingdom" },
  SG: { lat: 1.35, lng: 103.81, name: "Singapore" },
  SGP: { lat: 1.35, lng: 103.81, name: "Singapore" },
  Singapore: { lat: 1.35, lng: 103.81, name: "Singapore" },
  RO: { lat: 45.94, lng: 24.96, name: "Romania" },
  ROU: { lat: 45.94, lng: 24.96, name: "Romania" },
  Romania: { lat: 45.94, lng: 24.96, name: "Romania" },
  NG: { lat: 9.08, lng: 8.67, name: "Nigeria" },
  NGA: { lat: 9.08, lng: 8.67, name: "Nigeria" },
  Nigeria: { lat: 9.08, lng: 8.67, name: "Nigeria" },
  PA: { lat: 8.53, lng: -80.78, name: "Panama" },
  PAN: { lat: 8.53, lng: -80.78, name: "Panama" },
  Panama: { lat: 8.53, lng: -80.78, name: "Panama" },
  CY: { lat: 35.12, lng: 33.42, name: "Cyprus" },
  CYP: { lat: 35.12, lng: 33.42, name: "Cyprus" },
  Cyprus: { lat: 35.12, lng: 33.42, name: "Cyprus" },
  RU: { lat: 61.52, lng: 105.31, name: "Russia" },
  RUS: { lat: 61.52, lng: 105.31, name: "Russia" },
  Russia: { lat: 61.52, lng: 105.31, name: "Russia" },
  "Russian Federation": { lat: 61.52, lng: 105.31, name: "Russia" },
  IN: { lat: 20.59, lng: 78.96, name: "India" },
  IND: { lat: 20.59, lng: 78.96, name: "India" },
  India: { lat: 20.59, lng: 78.96, name: "India" },
  CA: { lat: 56.13, lng: -106.34, name: "Canada" },
  CAN: { lat: 56.13, lng: -106.34, name: "Canada" },
  Canada: { lat: 56.13, lng: -106.34, name: "Canada" },
  BR: { lat: -14.23, lng: -51.92, name: "Brazil" },
  BRA: { lat: -14.23, lng: -51.92, name: "Brazil" },
  Brazil: { lat: -14.23, lng: -51.92, name: "Brazil" },
  FR: { lat: 46.22, lng: 2.21, name: "France" },
  FRA: { lat: 46.22, lng: 2.21, name: "France" },
  France: { lat: 46.22, lng: 2.21, name: "France" },
  CN: { lat: 35.86, lng: 104.19, name: "China" },
  CHN: { lat: 35.86, lng: 104.19, name: "China" },
  China: { lat: 35.86, lng: 104.19, name: "China" },
  AU: { lat: -25.27, lng: 133.77, name: "Australia" },
  AUS: { lat: -25.27, lng: 133.77, name: "Australia" },
  Australia: { lat: -25.27, lng: 133.77, name: "Australia" },

  // Rest of Global Countries & Key Crypto / Financial Nodes
  AF: { lat: 33.93, lng: 67.71, name: "Afghanistan" },
  Afghanistan: { lat: 33.93, lng: 67.71, name: "Afghanistan" },
  AL: { lat: 41.15, lng: 20.16, name: "Albania" },
  Albania: { lat: 41.15, lng: 20.16, name: "Albania" },
  DZ: { lat: 28.03, lng: 1.65, name: "Algeria" },
  Algeria: { lat: 28.03, lng: 1.65, name: "Algeria" },
  AD: { lat: 42.50, lng: 1.52, name: "Andorra" },
  Andorra: { lat: 42.50, lng: 1.52, name: "Andorra" },
  AO: { lat: -11.20, lng: 17.87, name: "Angola" },
  Angola: { lat: -11.20, lng: 17.87, name: "Angola" },
  AR: { lat: -38.41, lng: -63.61, name: "Argentina" },
  Argentina: { lat: -38.41, lng: -63.61, name: "Argentina" },
  AM: { lat: 40.06, lng: 45.03, name: "Armenia" },
  Armenia: { lat: 40.06, lng: 45.03, name: "Armenia" },
  AT: { lat: 47.51, lng: 14.55, name: "Austria" },
  AUT: { lat: 47.51, lng: 14.55, name: "Austria" },
  Austria: { lat: 47.51, lng: 14.55, name: "Austria" },
  AZ: { lat: 40.14, lng: 47.57, name: "Azerbaijan" },
  Azerbaijan: { lat: 40.14, lng: 47.57, name: "Azerbaijan" },
  BS: { lat: 25.03, lng: -77.39, name: "Bahamas" },
  Bahamas: { lat: 25.03, lng: -77.39, name: "Bahamas" },
  BH: { lat: 26.06, lng: 50.55, name: "Bahrain" },
  Bahrain: { lat: 26.06, lng: 50.55, name: "Bahrain" },
  BD: { lat: 23.68, lng: 90.35, name: "Bangladesh" },
  Bangladesh: { lat: 23.68, lng: 90.35, name: "Bangladesh" },
  BB: { lat: 13.19, lng: -59.54, name: "Barbados" },
  Barbados: { lat: 13.19, lng: -59.54, name: "Barbados" },
  BY: { lat: 53.70, lng: 27.95, name: "Belarus" },
  Belarus: { lat: 53.70, lng: 27.95, name: "Belarus" },
  BE: { lat: 50.50, lng: 4.46, name: "Belgium" },
  BEL: { lat: 50.50, lng: 4.46, name: "Belgium" },
  Belgium: { lat: 50.50, lng: 4.46, name: "Belgium" },
  BZ: { lat: 17.18, lng: -88.49, name: "Belize" },
  Belize: { lat: 17.18, lng: -88.49, name: "Belize" },
  BM: { lat: 32.30, lng: -64.75, name: "Bermuda" },
  Bermuda: { lat: 32.30, lng: -64.75, name: "Bermuda" },
  BO: { lat: -16.29, lng: -63.58, name: "Bolivia" },
  Bolivia: { lat: -16.29, lng: -63.58, name: "Bolivia" },
  BA: { lat: 43.91, lng: 17.67, name: "Bosnia and Herzegovina" },
  "Bosnia and Herzegovina": { lat: 43.91, lng: 17.67, name: "Bosnia and Herzegovina" },
  BW: { lat: -22.32, lng: 24.68, name: "Botswana" },
  Botswana: { lat: -22.32, lng: 24.68, name: "Botswana" },
  VG: { lat: 18.42, lng: -64.64, name: "British Virgin Islands" },
  "British Virgin Islands": { lat: 18.42, lng: -64.64, name: "British Virgin Islands" },
  BVI: { lat: 18.42, lng: -64.64, name: "British Virgin Islands" },
  BG: { lat: 42.73, lng: 25.48, name: "Bulgaria" },
  BGR: { lat: 42.73, lng: 25.48, name: "Bulgaria" },
  Bulgaria: { lat: 42.73, lng: 25.48, name: "Bulgaria" },
  KH: { lat: 12.56, lng: 104.99, name: "Cambodia" },
  Cambodia: { lat: 12.56, lng: 104.99, name: "Cambodia" },
  CM: { lat: 7.36, lng: 12.35, name: "Cameroon" },
  Cameroon: { lat: 7.36, lng: 12.35, name: "Cameroon" },
  KY: { lat: 19.31, lng: -81.25, name: "Cayman Islands" },
  "Cayman Islands": { lat: 19.31, lng: -81.25, name: "Cayman Islands" },
  CL: { lat: -35.67, lng: -71.54, name: "Chile" },
  Chile: { lat: -35.67, lng: -71.54, name: "Chile" },
  CO: { lat: 4.57, lng: -74.29, name: "Colombia" },
  Colombia: { lat: 4.57, lng: -74.29, name: "Colombia" },
  CR: { lat: 9.74, lng: -83.75, name: "Costa Rica" },
  "Costa Rica": { lat: 9.74, lng: -83.75, name: "Costa Rica" },
  HR: { lat: 45.10, lng: 15.20, name: "Croatia" },
  Croatia: { lat: 45.10, lng: 15.20, name: "Croatia" },
  CU: { lat: 21.52, lng: -77.78, name: "Cuba" },
  Cuba: { lat: 21.52, lng: -77.78, name: "Cuba" },
  CZ: { lat: 49.81, lng: 15.47, name: "Czech Republic" },
  CZE: { lat: 49.81, lng: 15.47, name: "Czech Republic" },
  "Czech Republic": { lat: 49.81, lng: 15.47, name: "Czech Republic" },
  Czechia: { lat: 49.81, lng: 15.47, name: "Czech Republic" },
  DK: { lat: 56.26, lng: 9.50, name: "Denmark" },
  DNK: { lat: 56.26, lng: 9.50, name: "Denmark" },
  Denmark: { lat: 56.26, lng: 9.50, name: "Denmark" },
  DO: { lat: 18.73, lng: -70.16, name: "Dominican Republic" },
  "Dominican Republic": { lat: 18.73, lng: -70.16, name: "Dominican Republic" },
  EC: { lat: -1.83, lng: -78.18, name: "Ecuador" },
  Ecuador: { lat: -1.83, lng: -78.18, name: "Ecuador" },
  EG: { lat: 26.82, lng: 30.80, name: "Egypt" },
  Egypt: { lat: 26.82, lng: 30.80, name: "Egypt" },
  SV: { lat: 13.79, lng: -88.89, name: "El Salvador" },
  "El Salvador": { lat: 13.79, lng: -88.89, name: "El Salvador" },
  EE: { lat: 58.59, lng: 25.01, name: "Estonia" },
  EST: { lat: 58.59, lng: 25.01, name: "Estonia" },
  Estonia: { lat: 58.59, lng: 25.01, name: "Estonia" },
  ET: { lat: 9.14, lng: 40.48, name: "Ethiopia" },
  Ethiopia: { lat: 9.14, lng: 40.48, name: "Ethiopia" },
  FI: { lat: 61.92, lng: 25.74, name: "Finland" },
  FIN: { lat: 61.92, lng: 25.74, name: "Finland" },
  Finland: { lat: 61.92, lng: 25.74, name: "Finland" },
  GE: { lat: 42.31, lng: 43.35, name: "Georgia" },
  Georgia: { lat: 42.31, lng: 43.35, name: "Georgia" },
  GH: { lat: 7.94, lng: -1.02, name: "Ghana" },
  Ghana: { lat: 7.94, lng: -1.02, name: "Ghana" },
  GI: { lat: 36.14, lng: -5.35, name: "Gibraltar" },
  Gibraltar: { lat: 36.14, lng: -5.35, name: "Gibraltar" },
  GR: { lat: 39.07, lng: 21.82, name: "Greece" },
  GRC: { lat: 39.07, lng: 21.82, name: "Greece" },
  Greece: { lat: 39.07, lng: 21.82, name: "Greece" },
  GT: { lat: 15.78, lng: -90.23, name: "Guatemala" },
  Guatemala: { lat: 15.78, lng: -90.23, name: "Guatemala" },
  HK: { lat: 22.31, lng: 114.16, name: "Hong Kong" },
  HKG: { lat: 22.31, lng: 114.16, name: "Hong Kong" },
  "Hong Kong": { lat: 22.31, lng: 114.16, name: "Hong Kong" },
  HU: { lat: 47.16, lng: 19.50, name: "Hungary" },
  HUN: { lat: 47.16, lng: 19.50, name: "Hungary" },
  Hungary: { lat: 47.16, lng: 19.50, name: "Hungary" },
  IS: { lat: 64.96, lng: -19.02, name: "Iceland" },
  ISL: { lat: 64.96, lng: -19.02, name: "Iceland" },
  Iceland: { lat: 64.96, lng: -19.02, name: "Iceland" },
  ID: { lat: -0.78, lng: 113.92, name: "Indonesia" },
  IDN: { lat: -0.78, lng: 113.92, name: "Indonesia" },
  Indonesia: { lat: -0.78, lng: 113.92, name: "Indonesia" },
  IR: { lat: 32.42, lng: 53.68, name: "Iran" },
  Iran: { lat: 32.42, lng: 53.68, name: "Iran" },
  IQ: { lat: 33.22, lng: 43.67, name: "Iraq" },
  Iraq: { lat: 33.22, lng: 43.67, name: "Iraq" },
  IE: { lat: 53.14, lng: -7.69, name: "Ireland" },
  IRL: { lat: 53.14, lng: -7.69, name: "Ireland" },
  Ireland: { lat: 53.14, lng: -7.69, name: "Ireland" },
  IM: { lat: 54.23, lng: -4.54, name: "Isle of Man" },
  "Isle of Man": { lat: 54.23, lng: -4.54, name: "Isle of Man" },
  IL: { lat: 31.04, lng: 34.85, name: "Israel" },
  ISR: { lat: 31.04, lng: 34.85, name: "Israel" },
  Israel: { lat: 31.04, lng: 34.85, name: "Israel" },
  IT: { lat: 41.87, lng: 12.56, name: "Italy" },
  ITA: { lat: 41.87, lng: 12.56, name: "Italy" },
  Italy: { lat: 41.87, lng: 12.56, name: "Italy" },
  JM: { lat: 18.10, lng: -77.29, name: "Jamaica" },
  Jamaica: { lat: 18.10, lng: -77.29, name: "Jamaica" },
  JO: { lat: 30.58, lng: 36.23, name: "Jordan" },
  Jordan: { lat: 30.58, lng: 36.23, name: "Jordan" },
  KZ: { lat: 48.01, lng: 66.92, name: "Kazakhstan" },
  Kazakhstan: { lat: 48.01, lng: 66.92, name: "Kazakhstan" },
  KE: { lat: -0.02, lng: 37.90, name: "Kenya" },
  Kenya: { lat: -0.02, lng: 37.90, name: "Kenya" },
  KW: { lat: 29.31, lng: 47.48, name: "Kuwait" },
  Kuwait: { lat: 29.31, lng: 47.48, name: "Kuwait" },
  KG: { lat: 41.20, lng: 74.76, name: "Kyrgyzstan" },
  Kyrgyzstan: { lat: 41.20, lng: 74.76, name: "Kyrgyzstan" },
  LV: { lat: 56.87, lng: 24.60, name: "Latvia" },
  LVA: { lat: 56.87, lng: 24.60, name: "Latvia" },
  Latvia: { lat: 56.87, lng: 24.60, name: "Latvia" },
  LB: { lat: 33.85, lng: 35.86, name: "Lebanon" },
  Lebanon: { lat: 33.85, lng: 35.86, name: "Lebanon" },
  LI: { lat: 47.16, lng: 9.55, name: "Liechtenstein" },
  Liechtenstein: { lat: 47.16, lng: 9.55, name: "Liechtenstein" },
  LT: { lat: 55.16, lng: 23.88, name: "Lithuania" },
  LTU: { lat: 55.16, lng: 23.88, name: "Lithuania" },
  Lithuania: { lat: 55.16, lng: 23.88, name: "Lithuania" },
  LU: { lat: 49.81, lng: 6.12, name: "Luxembourg" },
  LUX: { lat: 49.81, lng: 6.12, name: "Luxembourg" },
  Luxembourg: { lat: 49.81, lng: 6.12, name: "Luxembourg" },
  MY: { lat: 4.21, lng: 101.97, name: "Malaysia" },
  MYS: { lat: 4.21, lng: 101.97, name: "Malaysia" },
  Malaysia: { lat: 4.21, lng: 101.97, name: "Malaysia" },
  MT: { lat: 35.93, lng: 14.37, name: "Malta" },
  MLT: { lat: 35.93, lng: 14.37, name: "Malta" },
  Malta: { lat: 35.93, lng: 14.37, name: "Malta" },
  MU: { lat: -20.34, lng: 57.55, name: "Mauritius" },
  Mauritius: { lat: -20.34, lng: 57.55, name: "Mauritius" },
  MX: { lat: 23.63, lng: -102.55, name: "Mexico" },
  MEX: { lat: 23.63, lng: -102.55, name: "Mexico" },
  Mexico: { lat: 23.63, lng: -102.55, name: "Mexico" },
  MD: { lat: 47.41, lng: 28.36, name: "Moldova" },
  Moldova: { lat: 47.41, lng: 28.36, name: "Moldova" },
  MC: { lat: 43.73, lng: 7.42, name: "Monaco" },
  Monaco: { lat: 43.73, lng: 7.42, name: "Monaco" },
  MN: { lat: 46.86, lng: 103.84, name: "Mongolia" },
  Mongolia: { lat: 46.86, lng: 103.84, name: "Mongolia" },
  ME: { lat: 42.70, lng: 19.37, name: "Montenegro" },
  Montenegro: { lat: 42.70, lng: 19.37, name: "Montenegro" },
  MA: { lat: 31.79, lng: -7.09, name: "Morocco" },
  Morocco: { lat: 31.79, lng: -7.09, name: "Morocco" },
  MM: { lat: 21.91, lng: 95.95, name: "Myanmar" },
  Myanmar: { lat: 21.91, lng: 95.95, name: "Myanmar" },
  NA: { lat: -22.95, lng: 18.49, name: "Namibia" },
  Namibia: { lat: -22.95, lng: 18.49, name: "Namibia" },
  NP: { lat: 28.39, lng: 84.12, name: "Nepal" },
  Nepal: { lat: 28.39, lng: 84.12, name: "Nepal" },
  NZ: { lat: -40.90, lng: 174.88, name: "New Zealand" },
  NZL: { lat: -40.90, lng: 174.88, name: "New Zealand" },
  "New Zealand": { lat: -40.90, lng: 174.88, name: "New Zealand" },
  MK: { lat: 41.60, lng: 21.74, name: "North Macedonia" },
  "North Macedonia": { lat: 41.60, lng: 21.74, name: "North Macedonia" },
  NO: { lat: 60.47, lng: 8.46, name: "Norway" },
  NOR: { lat: 60.47, lng: 8.46, name: "Norway" },
  Norway: { lat: 60.47, lng: 8.46, name: "Norway" },
  OM: { lat: 21.51, lng: 55.92, name: "Oman" },
  Oman: { lat: 21.51, lng: 55.92, name: "Oman" },
  PK: { lat: 30.37, lng: 69.34, name: "Pakistan" },
  Pakistan: { lat: 30.37, lng: 69.34, name: "Pakistan" },
  PY: { lat: -23.44, lng: -58.44, name: "Paraguay" },
  Paraguay: { lat: -23.44, lng: -58.44, name: "Paraguay" },
  PE: { lat: -9.18, lng: -75.01, name: "Peru" },
  Peru: { lat: -9.18, lng: -75.01, name: "Peru" },
  PH: { lat: 12.87, lng: 121.77, name: "Philippines" },
  PHL: { lat: 12.87, lng: 121.77, name: "Philippines" },
  Philippines: { lat: 12.87, lng: 121.77, name: "Philippines" },
  PL: { lat: 51.91, lng: 19.14, name: "Poland" },
  POL: { lat: 51.91, lng: 19.14, name: "Poland" },
  Poland: { lat: 51.91, lng: 19.14, name: "Poland" },
  PT: { lat: 39.39, lng: -8.22, name: "Portugal" },
  PRT: { lat: 39.39, lng: -8.22, name: "Portugal" },
  Portugal: { lat: 39.39, lng: -8.22, name: "Portugal" },
  PR: { lat: 18.22, lng: -66.59, name: "Puerto Rico" },
  "Puerto Rico": { lat: 18.22, lng: -66.59, name: "Puerto Rico" },
  QA: { lat: 25.35, lng: 51.18, name: "Qatar" },
  Qatar: { lat: 25.35, lng: 51.18, name: "Qatar" },
  SA: { lat: 23.88, lng: 45.07, name: "Saudi Arabia" },
  "Saudi Arabia": { lat: 23.88, lng: 45.07, name: "Saudi Arabia" },
  SN: { lat: 14.49, lng: -14.45, name: "Senegal" },
  Senegal: { lat: 14.49, lng: -14.45, name: "Senegal" },
  RS: { lat: 44.01, lng: 21.00, name: "Serbia" },
  Serbia: { lat: 44.01, lng: 21.00, name: "Serbia" },
  SC: { lat: -4.67, lng: 55.49, name: "Seychelles" },
  Seychelles: { lat: -4.67, lng: 55.49, name: "Seychelles" },
  SK: { lat: 48.66, lng: 19.69, name: "Slovakia" },
  SVK: { lat: 48.66, lng: 19.69, name: "Slovakia" },
  Slovakia: { lat: 48.66, lng: 19.69, name: "Slovakia" },
  SI: { lat: 46.15, lng: 14.99, name: "Slovenia" },
  SVN: { lat: 46.15, lng: 14.99, name: "Slovenia" },
  Slovenia: { lat: 46.15, lng: 14.99, name: "Slovenia" },
  ZA: { lat: -30.55, lng: 22.93, name: "South Africa" },
  ZAF: { lat: -30.55, lng: 22.93, name: "South Africa" },
  "South Africa": { lat: -30.55, lng: 22.93, name: "South Africa" },
  KR: { lat: 35.90, lng: 127.76, name: "South Korea" },
  KOR: { lat: 35.90, lng: 127.76, name: "South Korea" },
  "South Korea": { lat: 35.90, lng: 127.76, name: "South Korea" },
  Korea: { lat: 35.90, lng: 127.76, name: "South Korea" },
  "Republic of Korea": { lat: 35.90, lng: 127.76, name: "South Korea" },
  ES: { lat: 40.46, lng: -3.74, name: "Spain" },
  ESP: { lat: 40.46, lng: -3.74, name: "Spain" },
  Spain: { lat: 40.46, lng: -3.74, name: "Spain" },
  LK: { lat: 7.87, lng: 80.77, name: "Sri Lanka" },
  "Sri Lanka": { lat: 7.87, lng: 80.77, name: "Sri Lanka" },
  TW: { lat: 23.69, lng: 120.96, name: "Taiwan" },
  TWN: { lat: 23.69, lng: 120.96, name: "Taiwan" },
  Taiwan: { lat: 23.69, lng: 120.96, name: "Taiwan" },
  TH: { lat: 15.87, lng: 100.99, name: "Thailand" },
  THA: { lat: 15.87, lng: 100.99, name: "Thailand" },
  Thailand: { lat: 15.87, lng: 100.99, name: "Thailand" },
  TN: { lat: 33.88, lng: 9.53, name: "Tunisia" },
  Tunisia: { lat: 33.88, lng: 9.53, name: "Tunisia" },
  TR: { lat: 38.96, lng: 35.24, name: "Turkey" },
  TUR: { lat: 38.96, lng: 35.24, name: "Turkey" },
  Turkey: { lat: 38.96, lng: 35.24, name: "Turkey" },
  Turkiye: { lat: 38.96, lng: 35.24, name: "Turkey" },
  UA: { lat: 48.37, lng: 31.16, name: "Ukraine" },
  UKR: { lat: 48.37, lng: 31.16, name: "Ukraine" },
  Ukraine: { lat: 48.37, lng: 31.16, name: "Ukraine" },
  AE: { lat: 23.42, lng: 53.84, name: "United Arab Emirates" },
  ARE: { lat: 23.42, lng: 53.84, name: "United Arab Emirates" },
  UAE: { lat: 23.42, lng: 53.84, name: "United Arab Emirates" },
  "United Arab Emirates": { lat: 23.42, lng: 53.84, name: "United Arab Emirates" },
  Dubai: { lat: 25.20, lng: 55.27, name: "United Arab Emirates" },
  UY: { lat: -32.52, lng: -55.76, name: "Uruguay" },
  Uruguay: { lat: -32.52, lng: -55.76, name: "Uruguay" },
  UZ: { lat: 41.37, lng: 64.58, name: "Uzbekistan" },
  Uzbekistan: { lat: 41.37, lng: 64.58, name: "Uzbekistan" },
  VE: { lat: 6.42, lng: -66.58, name: "Venezuela" },
  Venezuela: { lat: 6.42, lng: -66.58, name: "Venezuela" },
  VN: { lat: 14.05, lng: 108.27, name: "Vietnam" },
  VNM: { lat: 14.05, lng: 108.27, name: "Vietnam" },
  Vietnam: { lat: 14.05, lng: 108.27, name: "Vietnam" },
  "Viet Nam": { lat: 14.05, lng: 108.27, name: "Vietnam" },
  ZW: { lat: -19.01, lng: 29.15, name: "Zimbabwe" },
  Zimbabwe: { lat: -19.01, lng: 29.15, name: "Zimbabwe" },
};

const locations = [
  { name: "USA", lat: 37.09, lng: -95.71 },
  { name: "Canada", lat: 56.13, lng: -106.34 },
  { name: "Germany", lat: 51.16, lng: 10.45 },
  { name: "Netherlands", lat: 52.13, lng: 5.29 },
  { name: "Nigeria", lat: 9.08, lng: 8.67 },
  { name: "Singapore", lat: 1.35, lng: 103.81 },
  { name: "Panama", lat: 8.53, lng: -80.78 },
  { name: "Switzerland", lat: 46.81, lng: 8.22 },
  { name: "Cyprus", lat: 35.12, lng: 33.42 },
  { name: "Russia", lat: 61.52, lng: 105.31 },
  { name: "India", lat: 20.59, lng: 78.96 },
  { name: "Japan", lat: 36.20, lng: 138.25 },
  { name: "Brazil", lat: -14.23, lng: -51.92 },
  { name: "Sweden", lat: 60.12, lng: 18.64 },
  { name: "Romania", lat: 45.94, lng: 24.96 },
  { name: "United Kingdom", lat: 55.37, lng: -3.43 },
];

// Set of normalized standard names so we don't duplicate them dynamically
const STANDARD_NAMES = new Set([
  "usa", "united states", "us",
  "canada", "ca",
  "germany", "de",
  "netherlands", "the netherlands", "holland", "nl",
  "nigeria", "ng",
  "singapore", "sg",
  "panama", "pa",
  "switzerland", "ch",
  "cyprus", "cy",
  "russia", "russian federation", "ru",
  "india", "in",
  "japan", "jp",
  "brazil", "br",
  "sweden", "se",
  "romania", "ro",
  "united kingdom", "uk", "great britain", "gb"
]);

/* =====================================================
   ROBUST GEOLOCATION RESOLVER (CAN SHOW ANY COUNTRY)
   ===================================================== */
export function getCountryCoordinates(raw: string): { lat: number; lng: number; name: string } {
  if (!raw || typeof raw !== "string") {
    return { lat: 37.09, lng: -95.71, name: "United States" };
  }

  const trimmed = raw.trim();
  if (!trimmed) {
    return { lat: 37.09, lng: -95.71, name: "United States" };
  }

  // 1. Direct key match
  if (countryCoordinates[trimmed]) {
    return countryCoordinates[trimmed];
  }

  // 2. Handle compound strings like "Global / Cayman Islands" or "Hong Kong / China"
  const parts = trimmed.split(/[/|,;()]+/).map((p) => p.trim()).filter(Boolean);
  for (const part of parts) {
    const pLow = part.toLowerCase();
    if (pLow === "global" || pLow === "unknown" || pLow === "custody" || pLow === "hub") continue;
    if (countryCoordinates[part]) {
      return countryCoordinates[part];
    }
  }

  // 3. Case-insensitive dictionary lookup
  const lower = trimmed.toLowerCase();
  for (const [key, val] of Object.entries(countryCoordinates)) {
    if (key.toLowerCase() === lower) {
      return val;
    }
  }

  // 4. Substring check for full names (e.g. "Federal Republic of Germany" -> "Germany")
  for (const [key, val] of Object.entries(countryCoordinates)) {
    if (key.length >= 4 && lower.includes(key.toLowerCase())) {
      return val;
    }
  }

  // 5. Fallback deterministic coordinate for unrecognized locations
  return { lat: 37.09, lng: -95.71, name: trimmed };
}

export function extractCountriesFromText(text: string): { lat: number; lng: number; name: string }[] {
  if (!text) return [];
  const found: { lat: number; lng: number; name: string }[] = [];
  const checked = new Set<string>();

  // Check country names / keys against text
  for (const [key, coords] of Object.entries(countryCoordinates)) {
    if (key.length < 3) continue; // skip 2-letter codes for broad text regex to prevent false positives
    const regex = new RegExp(`\\b${key}\\b`, "i");
    if (regex.test(text) && !checked.has(coords.name)) {
      checked.add(coords.name);
      found.push(coords);
    }
  }

  // Check 2-letter codes if prefixed or delimited (e.g., US, DE, NL)
  for (const [key, coords] of Object.entries(countryCoordinates)) {
    if (key.length === 2) {
      const codeRegex = new RegExp(`\\b${key}\\b`);
      if (codeRegex.test(text) && !checked.has(coords.name)) {
        checked.add(coords.name);
        found.push(coords);
      }
    }
  }

  return found;
}

/*
 * Your Earth texture is shifted approximately
 * 20 degrees east.
 *
 * Therefore the geographic longitude must be
 * shifted 20 degrees west before converting it
 * to the Three.js sphere coordinate.
 */
const TEXTURE_LONGITUDE_OFFSET = 20;

/* =====================================================
   LATITUDE / LONGITUDE → THREE.JS POSITION
   ===================================================== */

function pointOnGlobe(
  lat: number,
  lng: number,
  radius = 1.035
) {
  /*
   * Correct the longitude to match the
   * actual Earth texture.
   */
  const mappedLng =
    lng - TEXTURE_LONGITUDE_OFFSET;

  const latRad =
    THREE.MathUtils.degToRad(lat);

  const lngRad =
    THREE.MathUtils.degToRad(mappedLng);

  /*
   * This matches the UV orientation of
   * THREE.SphereGeometry.
   */
  return new THREE.Vector3(
    radius *
      Math.cos(latRad) *
      Math.cos(lngRad),

    radius *
      Math.sin(latRad),

    -radius *
      Math.cos(latRad) *
      Math.sin(lngRad)
  );
}

/* =====================================================
   COUNTRY LABEL
   ===================================================== */

function textSprite(text: string, isDiscreet = false) {
  const canvas =
    document.createElement("canvas");

  canvas.width = 512;
  canvas.height = 128;

  const context =
    canvas.getContext("2d")!;

  context.clearRect(
    0,
    0,
    canvas.width,
    canvas.height
  );

  context.font =
    isDiscreet ? "600 34px Inter, Arial" : "700 38px Inter, Arial";

  context.textAlign =
    "center";

  context.textBaseline =
    "middle";

  /* Text outline */
  context.lineWidth = 8;

  context.strokeStyle =
    "#031226";

  context.strokeText(
    text,
    canvas.width / 2,
    canvas.height / 2
  );

  /* Text */
  context.fillStyle =
    isDiscreet ? "#7dd3fc" : "#ffffff";

  context.fillText(
    text,
    canvas.width / 2,
    canvas.height / 2
  );

  const texture =
    new THREE.CanvasTexture(canvas);

  texture.colorSpace =
    THREE.SRGBColorSpace;

  const material =
    new THREE.SpriteMaterial({
      map: texture,

      transparent: true,

      /*
       * IMPORTANT:
       * The Earth can hide labels that
       * are on the back of the globe.
       */
      depthTest: true,
      depthWrite: false,
    });

  const sprite =
    new THREE.Sprite(material);

  /*
   * Bottom-center of label attaches
   * to the geographic position.
   */
  sprite.center.set(
    0.5,
    0
  );

  sprite.scale.set(
    isDiscreet ? 0.38 : 0.42,
    isDiscreet ? 0.095 : 0.105,
    1
  );

  return sprite;
}

/* =====================================================
   COUNTRY GLOBE
   ===================================================== */

export function CountryGlobe({
  alerts,
  playing,
  speed,
  liveEvents = [],
  activeCountries = [],
}: {
  alerts: Alert[];
  playing: boolean;
  speed: number;
  liveEvents?: NetworkEvent[];
  activeCountries?: string[];
}) {
  const host =
    useRef<HTMLDivElement>(null);

  const live =
    useRef(playing);

  const rate =
    useRef(speed);

  const liveGroupRef =
    useRef<THREE.Group | null>(null);

  const alertGroupRef =
    useRef<THREE.Group | null>(null);

  const dynamicGroupRef =
    useRef<THREE.Group | null>(null);

  live.current =
    playing;

  rate.current =
    speed;

  useEffect(() => {
    const element =
      host.current;

    if (!element) return;

    /* =================================================
       SCENE
       ================================================= */

    const scene =
      new THREE.Scene();

    /* =================================================
       CAMERA
       ================================================= */

    const camera =
      new THREE.PerspectiveCamera(
        38,
        1,
        0.1,
        100
      );

    camera.position.set(
      0,
      0.08,
      3.25
    );

    /* =================================================
       RENDERER
       ================================================= */

    const renderer =
      new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
      });

    renderer.setPixelRatio(
      Math.min(
        window.devicePixelRatio,
        2
      )
    );

    element.appendChild(
      renderer.domElement
    );

    /* =================================================
       GLOBE
       ================================================= */

    const globe =
      new THREE.Group();

    /*
     * Initial rotation only.
     * This does NOT affect the geographic
     * coordinate calculation.
     */
    globe.rotation.y =
      -0.38;

    const alertGroup =
      new THREE.Group();
    globe.add(alertGroup);
    alertGroupRef.current =
      alertGroup;

    const liveGroup =
      new THREE.Group();
    globe.add(liveGroup);
    liveGroupRef.current =
      liveGroup;

    const dynamicGroup =
      new THREE.Group();
    globe.add(dynamicGroup);
    dynamicGroupRef.current =
      dynamicGroup;

    scene.add(globe);

    /* =================================================
       EARTH TEXTURE
       ================================================= */

    const texture =
      new THREE.TextureLoader().load(
        "/assets/earth-equirectangular.png"
      );

    texture.colorSpace =
      THREE.SRGBColorSpace;

    /* =================================================
       EARTH
       ================================================= */

    const earth =
      new THREE.Mesh(
        new THREE.SphereGeometry(
          1,
          96,
          64
        ),

        new THREE.MeshPhongMaterial({
          map: texture,

          shininess: 12,

          specular:
            new THREE.Color(
              "#1b6da3"
            ),
        })
      );

    globe.add(earth);

    /* =================================================
       GLOW
       ================================================= */

    const glow =
      new THREE.Mesh(
        new THREE.SphereGeometry(
          1.025,
          96,
          64
        ),

        new THREE.MeshBasicMaterial({
          color:
            "#28c9ff",

          transparent:
            true,

          opacity:
            0.10,

          side:
            THREE.BackSide,
        })
      );

    globe.add(glow);

    /* =================================================
       LIGHTING
       ================================================= */

    scene.add(
      new THREE.AmbientLight(
        "#9edcff",
        1.5
      )
    );

    const light =
      new THREE.DirectionalLight(
        "#71d7ff",
        1.6
      );

    light.position.set(
      3,
      2,
      4
    );

    scene.add(light);

    /* =================================================
       COUNTRY MARKERS + LABELS
       ================================================= */

    locations.forEach(
      (location, index) => {

        /*
         * ---------------------------------------------
         * MARKER POSITION
         * ---------------------------------------------
         *
         * Both marker and label use exactly the
         * same corrected geographic position.
         */

        const markerPosition =
          pointOnGlobe(
            location.lat,
            location.lng,
            1.035
          );

        /* ---------------------------------------------
           MARKER
           --------------------------------------------- */

        const marker =
          new THREE.Mesh(
            new THREE.SphereGeometry(
              index < 3
                ? 0.03
                : 0.022,

              16,
              16
            ),

            new THREE.MeshBasicMaterial({
              color:
                index < 3
                  ? "#ff5267"
                  : "#53f5a0",
            })
          );

        marker.position.copy(
          markerPosition
        );

        globe.add(marker);

        /* ---------------------------------------------
           LABEL
           --------------------------------------------- */

        /*
         * Slightly farther from the globe,
         * but along the SAME radial direction.
         */
        const labelPosition =
          pointOnGlobe(
            location.lat,
            location.lng,
            1.075
          );

        const label =
          textSprite(
            location.name
          );

        label.position.copy(
          labelPosition
        );

        globe.add(label);
      }
    );

    /* =================================================
       RESIZE
       ================================================= */

    const resize = () => {
      const size =
        Math.min(
          element.clientWidth,
          410
        );

      renderer.setSize(
        size,
        size,
        false
      );

      camera.aspect =
        1;

      camera.updateProjectionMatrix();
    };

    resize();

    const observer =
      new ResizeObserver(
        resize
      );

    observer.observe(
      element
    );

    /* =================================================
       DRAGGING
       ================================================= */

    let dragging =
      false;

    let lastX = 0;
    let lastY = 0;

    const down = (
      event: PointerEvent
    ) => {
      dragging = true;

      lastX =
        event.clientX;

      lastY =
        event.clientY;

      renderer.domElement.setPointerCapture(
        event.pointerId
      );
    };

    const move = (
      event: PointerEvent
    ) => {
      if (!dragging)
        return;

      globe.rotation.y +=
        (event.clientX -
          lastX) *
        0.012;

      globe.rotation.x =
        THREE.MathUtils.clamp(
          globe.rotation.x +
            (event.clientY -
              lastY) *
              0.008,

          -0.55,
          0.55
        );

      lastX =
        event.clientX;

      lastY =
        event.clientY;
    };

    const up = () => {
      dragging = false;
    };

    renderer.domElement.addEventListener(
      "pointerdown",
      down
    );

    renderer.domElement.addEventListener(
      "pointermove",
      move
    );

    renderer.domElement.addEventListener(
      "pointerup",
      up
    );

    renderer.domElement.addEventListener(
      "pointercancel",
      up
    );

    /* =================================================
       ANIMATION
       ================================================= */

    let frame = 0;

    const animate = () => {
      frame =
        requestAnimationFrame(
          animate
        );

      if (
        live.current &&
        !dragging
      ) {
        globe.rotation.y +=
          0.0028 *
          rate.current;
      }

      renderer.render(
        scene,
        camera
      );
    };

    animate();

    /* =================================================
       CLEANUP
       ================================================= */

    return () => {
      cancelAnimationFrame(
        frame
      );

      observer.disconnect();

      renderer.domElement.removeEventListener(
        "pointerdown",
        down
      );

      renderer.domElement.removeEventListener(
        "pointermove",
        move
      );

      renderer.domElement.removeEventListener(
        "pointerup",
        up
      );

      renderer.domElement.removeEventListener(
        "pointercancel",
        up
      );

      texture.dispose();

      renderer.dispose();

      element.replaceChildren();
    };
  }, []);

  /* =================================================
     DYNAMIC ALERT CONNECTIONS (UPDATED WITHOUT RELOADING GLOBE)
     ================================================= */
  useEffect(() => {
    const alertGroup = alertGroupRef.current;
    if (!alertGroup) return;

    // Clear previous alert batch
    while (alertGroup.children.length > 0) {
      const child = alertGroup.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach(m => m.dispose());
        } else {
          child.material.dispose();
        }
      }
      alertGroup.remove(child);
    }

    if (!alerts || alerts.length === 0) return;

    alerts.slice(0, 10).forEach((alert, index) => {
      // Extract real countries involved from the alert's geo_summary
      const countriesInAlert = extractCountriesFromText(alert.geo_summary || "");

      let fromCoord = locations[index % locations.length];
      let toCoord = locations[(index + 3) % locations.length];

      if (countriesInAlert.length >= 2) {
        fromCoord = countriesInAlert[0];
        toCoord = countriesInAlert[1];
      } else if (countriesInAlert.length === 1) {
        fromCoord = countriesInAlert[0];
        toCoord = locations[(index + 4) % locations.length];
      }

      const from = pointOnGlobe(fromCoord.lat, fromCoord.lng, 1.035);
      const to = pointOnGlobe(toCoord.lat, toCoord.lng, 1.035);
      const middle = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(1.48);

      const curve = new THREE.QuadraticBezierCurve3(from, middle, to);
      const isTor = isDarknetOrTor(alert);
      const color = isTor ? "#c084fc" : getRisk(alert.risk_score).key === "high" ? "#ff5267" : "#ffc14d";

      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 30, isTor ? 0.015 : index === 0 ? 0.013 : 0.009, 6, false),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: isTor ? 0.98 : 0.92,
        })
      );

      alertGroup.add(tube);
    });
  }, [alerts]);

  /* =====================================================
     DISCREET DYNAMIC COUNTRIES
     Rest of world countries are added ONLY when they appear
     in current transactions, without initial map clutter.
     ===================================================== */
  useEffect(() => {
    const dynamicGroup = dynamicGroupRef.current;
    if (!dynamicGroup) return;

    // Clear dynamic group
    while (dynamicGroup.children.length > 0) {
      const child = dynamicGroup.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => m.dispose());
        } else {
          child.material.dispose();
        }
      }
      dynamicGroup.remove(child);
    }

    // Collect all unique country names from current transactions
    const discovered = new Set<string>();

    // 1. From live events
    liveEvents.forEach((ev) => {
      if (ev.src_geo_country) discovered.add(ev.src_geo_country);
      if (ev.dst_geo_country) discovered.add(ev.dst_geo_country);
    });

    // 2. From extra active countries list (e.g. hops, destinations)
    activeCountries.forEach((c) => {
      if (c) discovered.add(c);
    });

    // 3. From alerts
    alerts.slice(0, 10).forEach((al) => {
      const matched = extractCountriesFromText(al.geo_summary || "");
      matched.forEach((m) => discovered.add(m.name));
    });

    const renderedCoords = new Set<string>();

    discovered.forEach((countryStr) => {
      const coord = getCountryCoordinates(countryStr);
      if (!coord) return;

      const normName = coord.name.toLowerCase();
      // Skip if already in the 16 standard permanently rendered locations
      if (STANDARD_NAMES.has(normName) || STANDARD_NAMES.has(countryStr.toLowerCase())) {
        return;
      }

      // Avoid duplicates on dynamic layer
      const coordKey = `${coord.lat.toFixed(2)},${coord.lng.toFixed(2)}`;
      if (renderedCoords.has(coordKey)) return;
      renderedCoords.add(coordKey);

      // Add discreet marker
      const markerPos = pointOnGlobe(coord.lat, coord.lng, 1.035);
      const marker = new THREE.Mesh(
        new THREE.SphereGeometry(0.022, 16, 16),
        new THREE.MeshBasicMaterial({
          color: "#38bdf8", // subtle glowing sky-blue
        })
      );
      marker.position.copy(markerPos);
      dynamicGroup.add(marker);

      // Add discreet label
      const labelPos = pointOnGlobe(coord.lat, coord.lng, 1.075);
      const label = textSprite(coord.name, true);
      label.position.copy(labelPos);
      dynamicGroup.add(label);
    });
  }, [liveEvents, activeCountries, alerts]);

  /* =================================================
     DYNAMIC LIVE SIMULATION / REAL-TIME ARCS
     Every country in the world connects seamlessly.
     ================================================= */
  useEffect(() => {
    const liveGroup = liveGroupRef.current;
    if (!liveGroup) return;

    // Clear previous live batch
    while (liveGroup.children.length > 0) {
      const child = liveGroup.children[0] as THREE.Mesh;
      if (child.geometry) child.geometry.dispose();
      if (child.material) {
        if (Array.isArray(child.material)) {
          child.material.forEach((m) => m.dispose());
        } else {
          child.material.dispose();
        }
      }
      liveGroup.remove(child);
    }

    if (!liveEvents || liveEvents.length === 0) return;

    liveEvents.forEach((event) => {
      const srcCoord = getCountryCoordinates(event.src_geo_country);
      const dstCoord = getCountryCoordinates(event.dst_geo_country);
      if (!srcCoord || !dstCoord) return;

      const from = pointOnGlobe(srcCoord.lat, srcCoord.lng, 1.04);
      let to = pointOnGlobe(dstCoord.lat, dstCoord.lng, 1.04);

      // Handle internal country transaction (from and to in the same country)
      // Creates a localized elevated peer-relay arc rather than a degenerate curve
      if (from.distanceTo(to) < 0.02) {
        const tangent = new THREE.Vector3().crossVectors(from, new THREE.Vector3(0, 1, 0)).normalize();
        to = from.clone().addScaledVector(tangent, 0.06);
      }

      const middle = from.clone().add(to).multiplyScalar(0.5).normalize().multiplyScalar(1.52);
      const curve = new THREE.QuadraticBezierCurve3(from, middle, to);
      const isTor = isDarknetOrTor(event);
      const isAnomalous = event.event_id.includes("rapid") || event.event_id.includes("smurf");
      const color = isTor ? "#c084fc" : isAnomalous ? "#ff5267" : "#00f0ff";

      const tube = new THREE.Mesh(
        new THREE.TubeGeometry(curve, 32, isTor ? 0.015 : isAnomalous ? 0.012 : 0.007, 6, false),
        new THREE.MeshBasicMaterial({
          color,
          transparent: true,
          opacity: 0.95,
        })
      );
      liveGroup.add(tube);
    });
  }, [liveEvents]);

  return (
    <div className="globe-wrap">
      <div
        ref={host}
        className="three-globe"
      />

      <span>
        3D Earth drag to rotate
      </span>
    </div>
  );
}