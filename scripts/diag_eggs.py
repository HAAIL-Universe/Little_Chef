from app.services.inventory_agent import InventoryAgent
from app.services.proposal_store import ProposalStore

class S:
    def create_event(self, *a, **kw):
        pass

agent = InventoryAgent(S(), ProposalStore())
actions, w = agent._parse_inventory_actions("eggs ten pack six left best before 12 February")
for a in actions:
    e = a.event
    print(f"[{e.item_name}] qty={e.quantity} note={e.note}")
print(f"warnings: {w}")
