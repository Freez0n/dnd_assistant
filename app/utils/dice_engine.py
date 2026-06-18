import re
import random
from typing import List, Tuple, Optional

class DiceEngine:
    @staticmethod
    def calc_modifier(score: int) -> int:
        return (score - 10) // 2
    
    @staticmethod
    def parse_formula(formula: str) -> Tuple[List[Tuple[int, int]], int]:
        formula = formula.replace(" ", "").lower()
        
        if not re.match(r'^(\d*d\d+[+-]?\d*)+$', formula):
            raise ValueError(f"Неверная формула: {formula}")
        
        dice_parts = re.findall(r'(\d*)d(\d+)', formula)
        
        modifier_match = re.search(r'([+-]\d+)$', formula)
        modifier = int(modifier_match.group()) if modifier_match else 0
        
        dice = []
        for count, sides in dice_parts:
            count = int(count) if count else 1
            sides = int(sides)
            dice.append((count, sides))
        
        return dice, modifier
    
    @staticmethod
    def roll_dice(count: int, sides: int) -> List[int]:
        return [random.randint(1, sides) for _ in range(count)]
    
    @staticmethod
    def roll_formula(formula: str, advantage: bool = False, disadvantage: bool = False) -> Tuple[int, str, str]:
        try:
            dice, modifier = DiceEngine.parse_formula(formula)
            all_rolls = []
            total = 0
            details_parts = []
            
            for count, sides in dice:
                if sides == 20 and (advantage or disadvantage) and count == 1:
                    roll1 = random.randint(1, 20)
                    roll2 = random.randint(1, 20)
                    
                    if advantage:
                        result = max(roll1, roll2)
                        details_parts.append(f"🎲 d20 с преимуществом: [{roll1}, {roll2}] → {result}")
                    else:
                        result = min(roll1, roll2)
                        details_parts.append(f"🎲 d20 с помехой: [{roll1}, {roll2}] → {result}")
                    
                    all_rolls.append(result)
                    total += result
                else:
                    rolls = DiceEngine.roll_dice(count, sides)
                    all_rolls.extend(rolls)
                    total += sum(rolls)
                    
                    if count == 1:
                        details_parts.append(f"🎲 d{sides}: {rolls[0]}")
                    else:
                        details_parts.append(f"🎲 {count}d{sides}: {rolls} = {sum(rolls)}")
            
            if modifier != 0:
                sign = "+" if modifier > 0 else ""
                details_parts.append(f"Модификатор: {sign}{modifier}")
                total += modifier
            
            result_str = " | ".join(details_parts)
            if modifier != 0:
                sign = "+" if modifier > 0 else ""
                result_str += f" | Итого: {total} ({' + '.join(map(str, all_rolls))} {sign}{modifier})"
            else:
                result_str += f" | Итого: {total}"
            
            return total, result_str, formula
            
        except Exception as e:
            return 0, f"❌ Ошибка: {str(e)}", formula
    
    @staticmethod
    def roll_initiative(dex_modifier: int) -> int:
        roll = random.randint(1, 20)
        return roll + dex_modifier