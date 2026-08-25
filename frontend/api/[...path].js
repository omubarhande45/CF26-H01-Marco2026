import { proxyToGateway } from "./_proxy.js";

export default async function handler(req, res) {
  return proxyToGateway(req, res);
}
