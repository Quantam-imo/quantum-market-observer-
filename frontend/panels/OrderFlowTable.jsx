export default function OrderFlowTable({ ladder }) {
  return (
    <table className="orderflow-table">
      <thead>
        <tr>
          <th>Price</th>
          <th>Buy Qty</th>
          <th>Sell Qty</th>
          <th>Total</th>
          <th>Status</th>
        </tr>
      </thead>
      <tbody>
        {Object.entries(ladder).map(([price, data]) => (
          <tr key={price}>
            <td>{price}</td>
            <td>{data.buy_qty}</td>
            <td>{data.sell_qty}</td>
            <td>{data.total_qty}</td>
            <td>{data.absorbed ? "🧱 Absorbed" : "—"}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
