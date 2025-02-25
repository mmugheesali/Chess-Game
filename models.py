class Piece:
    def __init__(self,color,position,symbol):
        self.color=color
        self.position=position
        self.symbol=symbol
        
    def is_valid_move(self,move):
        pass;
    
class Pawn(Piece):
    def __init__(self,color,position,symbol):
        super.__init__(color,position,symbol)
        
    def is_valid_move(self,move):
        current_x,current_y=self.position
        new_x,new_y=move
        movement=new_y - current_y
        if current_x == new_x:
            if self.color == "white" :
                if current_y == 1:
                    if movement > 0 and movement < 3:
                        return True
                elif movement == 1:
                        return True
            else:
                if current_y == 7:
                    if movement > -3 and movement < 0:
                        return True
                elif movement == -1:
                    return True
        return False
    
class Rook(Piece):
    def __init__(self,color,position,symbol):
        super().__init__(color,position,symbol)
        
    def is_valid_move(self,move):
        current_x,current_y=self.position
        next_x,next_y=move
        y_movement=next_y - current_y
        x_movement=next_x - current_x
        if (x_movement == 0 and y_movement != 0) or (x_movement != 0 and y_movement == 0):
            return True
        return False
        
class Knight(Piece):
    def __init__(self,color,position,symbol):
        super().__init__(color,position,symbol)
        
    def is_valid_move(self,move):
        current_x,current_y=self.position
        next_x,next_y=move
        x_movement=next_x - current_x
        y_movement=next_y - current_y
        if x_movement != 0 and y_movement != 0:
            if y_movement > -3 and y_movement < 3 and x_movement > -3 and x_movement < 3:
                if (y_movement == 2 or y_movement == -2) and (x_movement == 1 or x_movement == -1):
                    return True
                if(y_movement == 1 or y_movement == -1) and (x_movement == 2 or x_movement == -2):
                    return True
        return False
    
class Bishop(Piece):
    def __init__(self,color,position,symbol):
        super().__init__(color,position,symbol)
        
    def is_valid_move(self, move):
        current_x,current_y = self.position
        next_x,next_y = move
        x_movement=next_x - current_x
        y_movement=next_y - current_y
        if x_movement == y_movement and x_movement != 0:
            return True
        return False
    
class Queen(Piece):
    def __init__(self,color,position,symbol):
        super().__init__(color,position,symbol)
        
    def is_valid_move(self,move):
        current_x,current_y = self.position
        next_x,next_y = move
        x_movement=next_x - current_x
        y_movement=next_y - current_y
        if (x_movement == 0 and y_movement != 0) or (x_movement != 0 and y_movement == 0):
            return True
        if x_movement == y_movement and x_movement != 0:
            return True
        return False

class King(Piece):
    def __init__(self,color,position,symbol):
        super().__init__(color,position,symbol)
        
    def is_valid_move(self,move):
        current_x,current_y = self.position
        next_x,next_y = move
        x_movement=next_x - current_x
        y_movement=next_y - current_y
        if x_movement != 0 or y_movement != 0:
            if x_movement > -2 and x_movement < 2 and y_movement > -2 and y_movement < 2:
                return True 
            